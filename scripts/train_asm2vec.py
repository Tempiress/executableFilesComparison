"""
Script to train asm2vec models on preprocessed data with different instruction modes.
Usage:
    python train_asm2vec.py --input train_data/generalize --output model_generalize.pt
"""

import sys
from pathlib import Path

# Add asm2vec_pytorch_master to path
asm2vec_root = Path(__file__).parent.parent / 'asm2vec_pytorch_master'
if str(asm2vec_root) not in sys.path:
    sys.path.insert(0, str(asm2vec_root))

import torch
import click
import asm2vec


@click.command()
@click.option('-i', '--input', 'ipath', help='Training data folder (preprocessed assembly)', required=True)
@click.option('-o', '--output', 'opath', default='model.pt', help='Output model path', show_default=True)
@click.option('-m', '--model', 'mpath', help='Load previous trained model path', type=str, default=None)
@click.option('-l', '--limit', help='Limit the number of functions to be loaded', show_default=True, type=int, default=None)
@click.option('-d', '--embedding-dimension', 'embedding_size', default=100, help='Embedding dimension', show_default=True)
@click.option('-b', '--batch-size', 'batch_size', default=1024, help='Batch size', show_default=True)
@click.option('-e', '--epochs', default=20, help='Training epochs', show_default=True)
@click.option('-n', '--neg-sample-num', 'neg_sample_num', default=25, help='Negative sampling amount', show_default=True)
@click.option('-c', '--device', default='auto', help='Hardware device: cpu / cuda / auto', show_default=True)
@click.option('-lr', '--learning-rate', 'lr', default=0.02, help="Learning rate", show_default=True)
@click.option('-s', '--save-every', 'save_every', default=5, help='Save model every N epochs', show_default=True)
def cli(ipath, opath, mpath, limit, embedding_size, batch_size, epochs, neg_sample_num, device, lr, save_every):
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    print(f" device: {device}")
    print(f" Training data: {ipath}")
    print(f" Output model: {opath}")
    
    if mpath:
        print(f" Loading model from: {mpath}")
        model, tokens = asm2vec.utils.load_model(mpath, device=device)
        functions, tokens_new = asm2vec.utils.load_data(ipath, limit=limit)
        tokens.update(tokens_new)
        model.update(len(functions), tokens.size())
    else:
        model = None
        functions, tokens = asm2vec.utils.load_data(ipath, limit=limit)
        print(f" Loaded {len(functions)} functions, {tokens.size()} tokens")
    
    # Train with intermediate saves
    def save_callback(context):
        epoch = context["epoch"]
        loss = context["loss"]
        progress = f'Epoch {epoch} | loss = {loss:.4f}'
        
        # Save intermediate model
        if epoch % save_every == 0 or epoch == epochs:
            save_path = f"{opath}.epoch_{epoch}"
            asm2vec.utils.save_model(save_path, context["model"], context["tokens"])
            progress += f" | saved to {save_path}"
        
        print(progress)
    
    model = asm2vec.utils.train(
        functions,
        tokens,
        model=model,
        embedding_size=embedding_size,
        batch_size=batch_size,
        epochs=epochs,
        neg_sample_num=neg_sample_num,
        device=device,
        callback=save_callback,
        learning_rate=lr
    )
    
    # Final save
    asm2vec.utils.save_model(opath, model, tokens)
    print(f"\n Final model saved to: {opath}")


if __name__ == '__main__':
    cli()
