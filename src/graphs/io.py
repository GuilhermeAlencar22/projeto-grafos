import pandas as pd

def load_airports(path):
    df = pd.read_csv(path)
    return df

def load_edges(path):
    df = pd.read_csv(path)
    return df