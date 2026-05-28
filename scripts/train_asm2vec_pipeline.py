"""
Full pipeline: preprocess binaries → train asm2vec models.
Preprocesses binaries with different instruction modes and trains corresponding models.
"""

import argparse
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """Run a command and check for errors."""
    print(f"\n{'='*60}")
    print(f" {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f" Error: {description} failed with code {result.returncode}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='Full pipeline: preprocess → train asm2vec models')
    parser.add_argument('-i', '--input', required=True, nargs='+',
                        help='Input directories with binaries')
    parser.add_argument('-o', '--output', default='asm2vec_models', help='Output directory for models')
    parser.add_argument('--data-dir', default='train_data', help='Directory for preprocessed data')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads for preprocessing')
    parser.add_argument('--epochs', type=int, default=20, help='Training epochs')
    parser.add_argument('--batch-size', type=int, default=1024, help='Batch size')
    parser.add_argument('--model-size', type=int, default=100, help='Embedding size')
    parser.add_argument('--neg-samples', type=int, default=25, help='Negative sampling')
    parser.add_argument('--lr', type=float, default=0.02, help='Learning rate')
    
    args = parser.parse_args()
    
    # Paths
    scripts_dir = Path(__file__).parent
    preprocess_script = scripts_dir / 'preprocess_train_data.py'
    train_script = scripts_dir / 'train_asm2vec.py'
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data_dirs = []
    
    # Step 1: Preprocess for each mode
    for mode in ['generalize', 'group', 'both']:
        print(f"\n{'#'*60}")
        print(f" ### Mode: {mode}")
        print(f"{'#'*60}")
        
        data_dir = Path(args.data_dir) / mode
        data_dirs.append(data_dir)
        
        # Run preprocessing
        cmd = (
            f"{sys.executable} {preprocess_script} "
            f"{' '.join([f'-i {d}' for d in args.input])} "
            f"-o {args.data_dir} -t {args.threads} --mode {mode}"
        )
        if not run_command(cmd, f"Preprocessing data for mode '{mode}'"):
            continue
        
        # Check if data generated
        if data_dir.exists() and list(data_dir.glob('*')):
            print(f" Data generated: {data_dir} ({len(list(data_dir.glob('*')))} files)")
            
            # Train model
            output_model = output_dir / f"model_{mode}.pt"
            
            print(f"\n Training model: {output_model}")
            cmd = (
                f"{sys.executable} {train_script} "
                f"-i {data_dir} -o {output_model} "
                f"-e {args.epochs} -b {args.batch_size} -d {args.model_size} "
                f"-n {args.neg_samples} -lr {args.lr}"
            )
            if not run_command(cmd, f"Training model '{mode}'"):
                continue
            
            print(f" Model saved: {output_model}")
        else:
            print(f" Warning: No data generated for mode '{mode}'")
    
    print(f"\n{'='*60}")
    print(f" Pipeline completed!")
    print(f" Models saved to: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
