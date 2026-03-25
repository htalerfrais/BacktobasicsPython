# simulation du comportement d'un log
# créer une fonction qui prend en paramètre une fonction

from functools import wraps

def my_function(func):
    # fonction wrapper de func qui retourne le résultat mais print des trucs en plus
    
    @wraps(func)
    def ajout_logs():
        print(f"avant fonction {func.__name__}")
        res = func("hello")
        print(f"après fonction {func.__name__}")
        return res
    
    return ajout_logs
 

@my_function
# la présence du décorateur évite d'avoir à configurer 
# text_is comme étant wrappée par my_function.
def text_is(text : str):
    print(f"text = {text}")
    return f"text = {text}"


# fonction définie dans une fonction

if __name__ == "__main__":
    
    # text_is = my_function(text_is)
    print(text_is())
    print(text_is.__name__)
