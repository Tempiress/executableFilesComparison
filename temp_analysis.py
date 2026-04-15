from collections import defaultdict

def analyze_results():
    data = defaultdict(list)
    
    with open('Debug/results.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith('result:'):
                continue
            
            # format: result: h_type: ssdeep // i_mode: generalize // c_mode: GPU // filename: 3mm: 0.0904 
            parts = line.split('//')
            if len(parts) >= 4:
                try:
                    h_type = parts[0].split('h_type:')[1].strip()
                    i_mode = parts[1].split('i_mode:')[1].strip()
                    c_mode = parts[2].split('c_mode:')[1].strip()
                    
                    filename_part = parts[3].split('filename:')[1].strip()
                    # for example "3mm: 0.0904"
                    filename, score_str = filename_part.rsplit(':', 1)
                    score = float(score_str.strip())
                    
                    key = f"Hash: {h_type} | Instr: {i_mode} | Compare: {c_mode}"
                    data[key].append(score)
                except Exception as e:
                    pass

    print("average similarity scores:")
    print("-" * 60)
    
    results = []
    for key, scores in data.items():
        avg = sum(scores) / len(scores)
        results.append((avg, key))
        
    # Sort by highest similarity
    results.sort(reverse=True)
    
    for avg, key in results:
        print(f"{avg:.4f}  <-  {key}")

if __name__ == '__main__':
    analyze_results()
