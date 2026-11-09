# cs2-tracked-bd2

Descriere domeniu

Aceasta este o aplicatie web creata pentru a monitoriza si inregistra statisticile jucatorilor de Counter-Strike 2.
Platforma o sa le permita utilizatorilor sa isi vada si analizeze performanta individuala(K(kill)/D(death) ratio, damage per round), istoricul meciurilor si sa se compare cu alti jucatori intr un leaderboard.


Descriere pagini de interfata
-Home(index): Va avea un formular de cautare(search bar) unde utilizatorii pot introduce profilul de Steam(SteamID) al oricariui utilizator steam pentru a le putea gasi statisticile
-Profile(Player Dashboard): Afiseaza stat asociate unui jucator si istoricul meciurilor jucate
-Leaderboard: Un top al celor mai buni jucatori inregistrati, ce poate fi filtrat in funct de diferite criterii
-Pagina de inregistrare/autentificare: Formular unde utilizatorii se inregistreaza sau logheza pe platforma
-Admin panel: Accesibil doar utilizatorilor cu rol specific sa gestioneze conturile si datele


Modelul de date propus
users: stocheza conturile aplicatiei web(username, parola hash)
roles: contine rolurile
players: stocheaza profilurile de CS2(SteamID, nume in game)
maps: stocheza info despre harti
matches: inregistreaza detaliile generate ale unui meci(data, scor final, harta jucata - relatie cu tabela maps)
player_match_stats: tabelul de legatura. asociaza jucatorul cu meciurile si va stoca statisticile


Etapa 2 Operații CRUD și Rute API
Toate cele 6 entitati ale bazei de date dispun de operatii complete CRUD (create, read, update, delete) expuse prin REST API si documentate interactiv in swagger UI (`/docs`):

Roles (`/roles`): `GET` (listare roluri), `POST` (adaugare rol nou), `PUT /{id}` (modificare descriere/nume rol), `DELETE /{id}` (stergere rol).

Users (`/users`): `GET` (listare utilizatori), `POST` (inregistrare utilizator), `PUT /{id}` (actualizare date/rol), `DELETE /{id}` (stergere cont).

Players (`/players`): `GET` (listare jucatori CS2), `POST` (adaugare profil Steam), `PUT /{id}` (actualizare nickname/avatar), `DELETE /{id}` (stergere jucator si statistici asociate in cascada).

Maps (`/maps`): `GET` (listare harti CS2), `POST` (adaugare harta), `PUT /{id}` (modificare status Active Duty), `DELETE /{id}` (stergere harta).

Matches (`/matches`): `GET` (istoric meciuri), `POST` (inregistrare meci nou), `PUT /{id}` (corectare scor CT/T), `DELETE /{id}` (stergere meci).

Player Match Stats (`/stats`): `GET` (listare statistici per meci), `POST` (adaugare Kills/Deaths/ADR pentru un jucator intr-un meci), `PUT /{id}` (actualizare statistici), `DELETE /{id}` (stergere linie statistica).



Etapa 3: Autentificare si Roluri (RBAC)
Implementarea Autentificarii
Stocarea parolelor: Parolele nu sunt stocate niciodata in clar. Se utilizeaza algoritmul criptografic `PBKDF2-HMAC-SHA256` cu 100.000 de iteratii si un `salt` aleatoriu de 16 bytes generat pentru fiecare utilizator (format `salt$hash`).

Sesiuni / Tokenuri: Autentificarea se realizeaza prin ruta `POST /login` (OAuth2 Password Flow) care returneaza un token JWT (JSON Web Token) semnat cu `HS256`, valabil 60 de minute. Tokenul contine identitatea utilizatorului (`sub`) si rolul acestuia (`role`).

Cele 3 Roluri si Drepturile de Acces
1. Standard (`casual_user` / parola: `standard123`)**:
    Poate vizualiza statisticile publice, jucatorii, hartile si meciurile (`GET`).
    Isi poate verifica propriul profil prin ruta `/me`.
    Nu poate sterge sau modifica date si nu are acces la ruta `/analytics/advanced`.
2. Premium (`pro_player` / parola: `premium123`)**:
    Are toate drepturile rolului Standard.
    Are acces la statistici avansate prin ruta `/analytics/advanced`.
    Poate adauga si actualiza jucatori, meciuri si statistici (`POST`, `PUT` pe `/players`, `/matches`, `/stats`).
3. Admin (`admin_cs2` / parola: `admin123`)**:
    Control complet asupra tuturor celor 6 entitati.
    Singurul rol care poate sterge inregistrari (`DELETE`), gestiona roluri (`/roles`), harti (`/maps`) si vedea/modifica toti utilizatorii (`/users`).