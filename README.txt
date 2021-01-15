Istnieją dwie zasady.
1. CSS nie istnieje
2. CSS nie istnieje

Ograniczyłem się do zrealizowania możliwie porządnie wszystkich funkcjonalności, niekoniecznie sprawiając aby wyglądały pięknie od strony graficznej.


Zastosowany stos technologiczny
===============================

FlaskWTF
--------
Biblioteka do automatyzacji tworzenia i walidacji formularzy. Implementuje funkcjonalność tokenu CSRF. W templatkach może Pan zobaczyć wielokrotnie "{{ form.csrf_token }}".

FlaskLogin
----------
Automatyzacja logowania, utrzymywania sesji, przedawniania się sesji. Dodatkowo dostarcza "current_user" oraz "login_required".

PyCryptoDome
------------
Wszelakie kwestie związane z kryptografią obsługiwane poprzez tą bibliotekę.
-> Hashowanie haseł: pbkdf2_sha256.hash
 - implementuje 16 bajtową sól oraz wielokrotne hashowanie (29000 rund)
 - od siebie dodatkowo dodałem pieprz który można dodać w konfiguracji
-> Szyfrowanie notatek i plików: AES, mode.EAX (encrypt-then-authenticate-then-translate)


Dodatkowe informacje
====================
Nie dodaję do repozytorium plików z certyfikatem i kluczem RSA. Te pliki będą dostępne w paczce na ISOD, ale nie w publicznym repozytorium.