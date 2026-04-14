# FTP-Metashape
Wtyczka do Agisoft Metashape do automatycznej orientacji zdjęć oraz generowania chmury punktów i modeli 3D.
# Automatyczna orientacja zdjęć w Metashape


## Funkcjonalność

* wybór folderu ze zdjęciami
* wczytywanie punktów osnowy z pliku tekstowego
* wybór układów współrzędnych (EPSG)
* transformacja współrzędnych kamer i punktów
* automatyczna orientacja zdjęć
* detekcja markerów
* dopasowanie punktów kontrolnych do wykrytych markerów
* opcjonalne generowanie:

  * gęstej chmury punktów
  * modelu 3D (mesh)
  * tekstury

## Jak działa

Po uruchomieniu użytkownik wskazuje dane wejściowe oraz parametry przetwarzania. Skrypt tworzy nowy projekt, wczytuje zdjęcia i punkty kontrolne, a następnie wykonuje orientację zdjęć.

Punkty osnowy są transformowane do wybranego układu współrzędnych i przypisywane do markerów. W przypadku wykrycia odpowiadających punktów w danych obrazowych następuje ich automatyczne dopasowanie.

Na końcu możliwe jest wygenerowanie produktów końcowych (dense cloud, mesh, tekstura) oraz zapis projektu.

## Struktura

```
main.py    – logika przetwarzania i integracja z Metashape  
gui3.py    – interfejs użytkownika (PyQt)  
```

## Uruchomienie

Skrypt należy dodać do środowiska Metashape jako plugin. Po uruchomieniu pojawi się w menu:

FTP → Automatyczna orientacja

## Wymagania

* Agisoft Metashape
* Python (zgodny z wersją Metashape)
* PyQt5

## Dane wejściowe

Plik z punktami osnowy powinien mieć format:

```
ID X Y Z
```
