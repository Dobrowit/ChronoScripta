https://chatgpt.com/canvas/shared/67a71e202f808191902c7091601d971e

Potrzebuję mały system (aplikację) do zarządzania dokumentacją. Ma być napisana w python. Ma działać w trybie tekstowym (w konsoli). Ma mieć następujące funkcje:

  - baza danych z metadanymi plików prowadzona i zapisywana w formacie JSON

  - ma obsługiwać dwa foldery "dropit" i "storage"

  - do folderu "dropit" wrzuca się nowe dokumentu; skrypt okresowo lub po ręcznym wyzwoleniu sprawdza ten folder i przenosi pliki do katalogu "storage" umieszczając je w podkatalogach zgodnie z datą dokumentu wg schematu /storage/rok/miesiac/dzien.rozszerzenie; przykład: /storage/2023/04/12.pdf

  - przed przeniesieniem trzeba zebrać metadane, które wpisuje się ręcznie: opis dokumentu, data dokumentu, autor dokumentu, adresat dokumentu; z tymi danymi powiązany jest plik dokumentu (jego ścieżka w "storage"); z automatu dodawane są jeszcze następujące informacje: suma kontrolna md5; format pliku (pdf; doc; odt itp); numer kolejny w bazie (index).

  - przed ręcznym wprowadzeniem metadanych skrypt w tle otwiera plik za pomocą odpowiedniej przeglądarki lub programu aby operator mógł odczytać ten dokument podczas wprowadzania metadanych

  - jeśli po sprawdzeniu sumy kontrolnej md5 okaże się że plik jest już w bazie i w folderze "storage"; wyświetla się stosowny komunikat o duplikacie; plik nie jest ponownie dodawany; suma kontrolna i czy istnieje duplikat musi być sprawdzane przed uruchomieniem wpisywania metadanych

  - po procesie dodania plik źródłowy znika z folderu "dropit" i jeśli nie jest duplikatem - pojawia się w "storage" po spełnieniu wcześniejszych reguł

 - aplikacja ma proste menu tekstowe; opcje wybiera się poprzez podanie numeru pozycji menu; oto menu z uwzględnieniem funkcjonalności:
1. Przeskanuj folder "drop it"
2. Obserwuj folder "drop it" w sposób ciągły (do przerwania kombinacją CTRL+c)
3. Pokaż statystyki (ilość plików; objętość plików; pięć największych plików)
4. Spakuj cały folder "storage" wraz z bazą danych do pliku archiwum ZIP
5. Pokaż listę plików w "storage"
6. Szukaj pliku w "storage" po wszystkich polach w bazie
7. Koniec

Opcje 5 i 6 pozwalają wybrać plik z listy (poprzez wprowadzenie jego numeru z listy) i otworzyć go.
