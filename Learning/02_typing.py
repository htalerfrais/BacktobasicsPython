from typing import List, Optional, Union

def tokenize(word : str) -> List[str]:
    return word.split()


if __name__ == "__main__":
    print(f"résultat de tokenisation de {"getting "} : {tokenize("getting")}")
    print(f"{tokenize("getting")[0]}")