"""
Script to preprocess binary files for asm2vec training with different instruction modes.
Generates preprocessed assembly files in train_data_generalize, train_data_group, train_data_both.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from multiprocessing import Pool

# Add project root to path
project_root = Path(__file__).parent.parent
asm2vec_root = Path(__file__).parent.parent / 'asm2vec_pytorch_master'
for _p in [str(project_root), str(asm2vec_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import r2pipe
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def preprocess_function(args):
    """Preprocess a single binary file."""
    file_path, output_base, mode = args
    
    if not file_path.exists() or not file_path.is_file():
        return None
    
    try:
        with open(file_path, 'rb') as f:
            header = f.read(4)
        # Accept ELF (Linux) or MZ (Windows)
        is_valid = (header[:2] == bytes.fromhex('4d5a')) or (header[:4] == bytes.fromhex('7f454c46'))
        if not is_valid:
            return None
    except:
        return None
    
    try:
        r = r2pipe.open(str(file_path), flags=["-2"])
        r.cmd('aaaa')
        
        functions = r.cmdj('aflj')
        if not functions:
            r.quit()
            return None
        
        output_subdir = output_base / mode
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for fn in functions:
            func_addr = fn['addr']
            func_name = fn.get('name', f"func_{func_addr:x}")
            safe_name = func_name.replace('<', '_').replace('>', '_').replace('=', '_')
            
            ops_json = r.cmdj(f'pdfj @ {func_addr}')
            if not ops_json or not ops_json.get('ops'):
                continue
            
            ops = ops_json['ops']
            output_lines = []
            
            for op in ops:
                if 'invalid' in op.get('type', ''):
                    continue
                    
                full_opcode = op.get('opcode') or op.get('disasm', '')
                if not full_opcode:
                    continue
                
                if mode == 'generalize':
                    import opcodeparser
                    full_opcode = opcodeparser.generalize_opcode(full_opcode)
                elif mode == 'group':
                    import opcodeparser
                    gi = opcodeparser.GroupInstructions()
                    op_type = op.get('type', '')
                    if op_type:
                        group = gi.find_group(op_type)
                        if group:
                            parts = full_opcode.split(maxsplit=1)
                            if len(parts) > 1:
                                full_opcode = f"{group} {parts[1]}"
                            else:
                                full_opcode = group
                elif mode == 'both':
                    import opcodeparser
                    full_opcode = opcodeparser.generalize_opcode(full_opcode)
                    gi = opcodeparser.GroupInstructions()
                    op_type = op.get('type', '')
                    if op_type:
                        group = gi.find_group(op_type)
                        if group:
                            parts = full_opcode.split(maxsplit=1)
                            if len(parts) > 1:
                                full_opcode = f"{group} {parts[1]}"
                            else:
                                full_opcode = group
                
                output_lines.append(full_opcode)
            
            if len(output_lines) > 10:
                asm_content = '\n'.join(output_lines)
                # Use gcc -S compatible format with metadata
                header = f'.name {safe_name}\n.file {file_path.name}\n'
                full_asm = header + asm_content
                asm_file = output_subdir / safe_name
                with open(asm_file, 'w', encoding='utf-8') as f:
                    f.write(full_asm)
                count += 1
        
        r.quit()
        return {'file': file_path.name, 'count': count, 'mode': mode}
        
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return None


def collect_binaries(bin_dirs):
    """Collect all binary files from directories."""
    binaries = []
    for bin_dir in bin_dirs:
        if not Path(bin_dir).exists():
            logging.warning(f"Directory not found: {bin_dir}")
            continue
        for root, dirs, files in os.walk(bin_dir):
            for f in files:
                fpath = Path(root) / f
                # Skip .nam files (they are metadata, not binaries)
                if fpath.suffix == '.nam':
                    continue
                # Accept all other files (including no extension)
                binaries.append(fpath)
    return binaries


def main():
    parser = argparse.ArgumentParser(description='Preprocess binaries for asm2vec training')
    parser.add_argument('-i', '--input', required=True, nargs='+',
                        help='Input directories with binaries (e.g., coreutils-polybench-hashcat)')
    parser.add_argument('-o', '--output', default='train_data', help='Output base directory')
    parser.add_argument('--threads', type=int, default=4, help='Number of parallel threads')
    parser.add_argument('--mode', choices=['generalize', 'group', 'both', 'all'], default='all',
                        help='Preprocessing mode(s)')
    
    args = parser.parse_args()
    
    output_base = Path(args.output)
    modes = ['generalize', 'group', 'both'] if args.mode == 'all' else [args.mode]
    
    logging.info(f"Collecting binaries from {args.input}...")
    binaries = collect_binaries(args.input)
    logging.info(f"Found {len(binaries)} binaries")
    
    for mode in modes:
        logging.info(f"\n=== Processing mode: {mode} ===")
        output_dir = output_base / mode
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)
        
        logging.info(f"Preprocessing with {args.threads} threads...")
        with Pool(processes=min(args.threads, len(binaries))) as pool:
            results = pool.map(preprocess_function, [(b, output_base, mode) for b in binaries])
        
        valid_results = [r for r in results if r is not None]
        total_files = sum(r['count'] for r in valid_results)
        logging.info(f"Mode {mode}: Processed {len(valid_results)} files, {total_files} functions")


if __name__ == '__main__':
    main()
