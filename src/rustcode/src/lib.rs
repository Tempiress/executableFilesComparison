use pyo3::prelude::*;
use pyo3::types::PyDict;
use strsim::levenshtein;
use std::collections::HashSet;

// Структура для хранения данных одного базового блока
struct BlockData {
    id: i32,
    address: u64,
    fuzzyhash: String,
    hash: String,
    number_group: String,
}

// Простая функция для извлечения полей из словаря Python (PyDict)
fn extract_block(val_dict: &PyDict) -> BlockData {
    let mut id = 0;
    let mut address = 0;
    let mut fuzzyhash = String::new();
    let mut hash = String::new();
    let mut number_group = String::new();

    // Извлекаем ID блока
    if let Ok(Some(item)) = val_dict.get_item("id") {
        if let Ok(val) = item.extract::<i32>() {
            id = val;
        }
    }

    // Извлекаем адрес блока
    if let Ok(Some(item)) = val_dict.get_item("block") {
        if let Ok(val) = item.extract::<u64>() {
            address = val;
        }
    }

    // Извлекаем нечеткий хэш (ssdeep/tlsh/nilsimsa)
    if let Ok(Some(item)) = val_dict.get_item("fuzzyhash") {
        if let Ok(val) = item.extract::<String>() {
            fuzzyhash = val;
        }
    }

    // Извлекаем точный хэш
    if let Ok(Some(item)) = val_dict.get_item("hash") {
        if let Ok(val) = item.extract::<String>() {
            hash = val;
        }
    }

    // Извлекаем последовательность операндов
    if let Ok(Some(item)) = val_dict.get_item("number_group") {
        if let Ok(val) = item.extract::<String>() {
            number_group = val;
        }
    }

    BlockData {
        id,
        address,
        fuzzyhash,
        hash,
        number_group,
    }
}

// Преобразуем словарь Python (PyDict) в простой динамический массив Rust (Vec<BlockData>)
fn parse_python_blocks(dict: &PyDict) -> Vec<BlockData> {
    let mut list = Vec::new();
    for (_, val) in dict.iter() {
        if let Ok(val_dict) = val.downcast::<PyDict>() {
            list.push(extract_block(val_dict));
        }
    }
    list
}

// Быстрое сравнение 256-битных Nilsimsa-хэшей в формате HEX
fn compare_nilsimsa_diff(h1: &str, h2: &str) -> i32 {
    let mut bytes1 = Vec::new();
    let mut bytes2 = Vec::new();

    // Переводим HEX-строку h1 в массив байт
    let clean1: String = h1.chars().filter(|c| c.is_ascii_hexdigit()).collect();
    for chunk in clean1.as_bytes().chunks(2) {
        if chunk.len() == 2 {
            if let Ok(s) = std::str::from_utf8(chunk) {
                if let Ok(b) = u8::from_str_radix(s, 16) {
                    bytes1.push(b);
                }
            }
        }
    }

    // Переводим HEX-строку h2 в массив байт
    let clean2: String = h2.chars().filter(|c| c.is_ascii_hexdigit()).collect();
    for chunk in clean2.as_bytes().chunks(2) {
        if chunk.len() == 2 {
            if let Ok(s) = std::str::from_utf8(chunk) {
                if let Ok(b) = u8::from_str_radix(s, 16) {
                    bytes2.push(b);
                }
            }
        }
    }

    if bytes1.len() != 32 || bytes2.len() != 32 {
        return 128; // Нейтральная разница при некорректной длине
    }

    // Считаем количество отличающихся битов
    let mut diff_bits = 0;
    for i in 0..32 {
        diff_bits += (bytes1[i] ^ bytes2[i]).count_ones();
    }
    diff_bits as i32
}

#[pyfunction]
fn match_similar_blocks_rust(
    py: Python,
    blocks_a: &PyDict,
    blocks_b: &PyDict,
    instructions_mode: String,
    hash_type: String,
) -> PyResult<Vec<(i32, i32, i32, i32)>> {
    // Извлекаем блоки из словарей Python
    let list_a = parse_python_blocks(blocks_a);
    let list_b = parse_python_blocks(blocks_b);

    // Получаем доступ к Python-функциям для ssdeep/tlsh/fuzz
    let hashing_mod = py.import("src.core.hashing")?;
    let ssdeep_fn = hashing_mod.getattr("cached_ppdeep_compare")?;
    let tlsh_fn = hashing_mod.getattr("lazy_tlsh_diff")?;
    let fuzz_fn = hashing_mod.getattr("lazy_fuzz_ratio")?;

    let mut all_pairs = Vec::new();

    // Сравниваем каждый блок из A с каждым блоком из B
    for a in &list_a {
        for b in &list_b {
            let hash_equal = if a.hash == b.hash { 1 } else { 0 };
            let same_address = if a.address == b.address { 1 } else { 0 };

            let mut similarity = 0;
            let mut edit_dist = 0;

            if hash_equal == 1 {
                similarity = 100;
            } else {
                edit_dist = levenshtein(&a.number_group, &b.number_group) as i32;

                if instructions_mode != "group_only" {
                    // если один из хэшей пустой, НЕ вызываем C-библиотеку!
                    if a.fuzzyhash.is_empty() || b.fuzzyhash.is_empty() {
                        similarity = 0;
                    } else if hash_type == "nilsimsa" {
                        let diff_bits = compare_nilsimsa_diff(&a.fuzzyhash, &b.fuzzyhash);
                        let cmp_val = 128 - diff_bits;
                        similarity = std::cmp::min(100, cmp_val * 100 / 128);
                    } else {
                        // Очищаем пул объектов Python на каждой итерации
                        let _pool = unsafe { py.new_pool() };
                        let res: PyResult<i32> = if hash_type == "ssdeep" {
                            ssdeep_fn.call1((&a.fuzzyhash, &b.fuzzyhash))?.extract()
                        } else if hash_type == "tlsh" {
                            tlsh_fn.call1((&a.fuzzyhash, &b.fuzzyhash))?.extract()
                        } else {
                            fuzz_fn.call1((&a.fuzzyhash, &b.fuzzyhash))?.extract()
                        };

                        if let Ok(val) = res {
                            similarity = val;
                        }
                    }
                }
            }

            // Запоминаем результат пары
            all_pairs.push((hash_equal, same_address, similarity, -edit_dist, a.id, b.id));
        }
    }

    // Сортируем все найденные пары по убыванию похожести
    all_pairs.sort_by(|x, y| y.cmp(x));

    // Жадный выбор сопоставлений (каждый блок сопоставляется не более одного раза)
    let mut matched = Vec::new();
    let mut used_a = HashSet::new();
    let mut used_b = HashSet::new();

    for pair in all_pairs {
        let id_a = pair.4;
        let id_b = pair.5;
        if !used_a.contains(&id_a) && !used_b.contains(&id_b) {
            matched.push((id_a, id_b, pair.2, pair.0));
            used_a.insert(id_a);
            used_b.insert(id_b);
        }
    }

    Ok(matched)
}

#[pymodule]
fn code_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(match_similar_blocks_rust, m)?)?;
    Ok(())
}