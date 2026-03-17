import random 
import string
from dataclasses import dataclass, field

def generate_id() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=12))

@dataclass(frozen=True)
class Person:
    name : str
    age : int
    active : bool = True
    email_adresses : list[str] = field(default_factory=list) # default value that must not lead to the same empty list for all user who don't have email adress
    id: str = field(init = False, default_factory=generate_id) # init  = False so that id can't be provided by the initialliser
    _search_string: str = field(init=False, repr=False) # string containing content we can search the instance with
    
    def __post_init__(self) -> None:
        # method creating the internal instance variables, not supposed to be changed outside of the class
        # here it is generated during class initialisation
        object.__setattr__(self, "_search_string", f"{self.name} {self.age}")
             

def main():
    person = Person(name = "Preston", age = 24)
    # person.name = "Hector" # not applied because the dataclass Person is frozen & immutable.
    print(person)
    
if __name__ == "__main__":
    main()