from abc import ABC, abstractmethod


class Vehicle(ABC):
    # this class can't be instanciated by itself

    # abstract methods are mendatoryi for children classes inheriting from vehicles.
    @abstractmethod
    def work(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass
    
    
class Truck(Vehicle):
    def work(self):
        print("truck working")
        
    def stop(self):
        print("truck stopping")
        
class Moto(Vehicle):
    def work(self):
        print("moto avance")
        
    def stop(self):
        print("moto se stop")
    
if __name__ == "__main__":
    voiture = Truck()
    moto = Moto()
    
    voiture.work()
    moto.work()
    voiture.stop()
    moto.stop()