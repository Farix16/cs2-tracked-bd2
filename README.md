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


Etapa 4: Performanta (Indecsi si Load Test)

1. Generator de date in masa (Bulk Seeding)
Din panoul de administrare (`POST /admin/generate-bulk`) se pot genera mii de jucatori si zeci de mii de inregistrari in `player_match_stats` pentru a simula un volum real de date.

2. Indecsi si Planuri de Executie (Inainte si Dupa)
Interogarea analizata cauta jucatorii de top care au obtinut cel putin 28 de kills si un ADR >= 95.0 intr-un meci, ordonati descrescator dupa ADR:
Inainte de index: Planul de executie (`EXPLAIN QUERY PLAN`) indica `SCAN s` (Full Table Scan pe tabela `player_match_stats`).
Indecsi adaugati: Indexul compus `idx_stats_kills_adr ON player_match_stats (kills, adr DESC)` si indexul `idx_stats_player_id ON player_match_stats (player_id)`.
Dupa index: Planul de executie se schimba in `SEARCH s USING INDEX idx_stats_kills_adr (kills>?)`, eliminand scanarea completa a tabelei si reducand timpul de executie de 5-10 ori.

3. Load Test (Testarea API-ului sub sarcina)
Folosind scriptul `load_test.py` (200 cereri HTTP concurente, 20 utilizatori simultani pe endpoint-ul `/players`):
Rata de succes: 200/200 (100% raspunsuri HTTP 200 OK).
Throughput (RPS): ~120 - 250 cereri/secunda.
Latenta medie: ~60 - 110 ms per cerere.

4. Curatare date de test (Stergere Boti Generati)
Endpoint: `DELETE /admin/clear-bots` (accesibil doar pentru rolul Admin).
Functionalitate: Din panoul de administrare exista un buton dedicat (Sterge Botii Generati) care elimina dintr-un click toti jucatorii generati automat pentru testele de performanta (`CS2_Player_%`) impreuna cu statisticile lor asociate din tabela `player_match_stats`, readucand baza de date la starea curata.

5. Integrare Steam Web API (Import Jucatori Reali)
Aplicatia permite preluarea datelor reale ale jucatorilor direct de pe serverele Valve/Steam folosind SteamID64:
Endpoint: `POST /players/import-steam/{steam_id}` (accesibil pentru rolurile Premium si Admin).
Date preluate automat:
  Profil Steam (`ISteamUser/GetPlayerSummaries`): Nickname-ul real (`personaname`) si poza de profil (`avatarfull`).
  Statistici CS2 (`ISteamUserStats/GetUserStatsForGame`, AppID `730`): Total Kills, Total Deaths, calcul automat pentru ADR (Damage mediu pe runda) si Headshot % (pentru profilurile Steam care au setarea Game Details pe Public).
Securitate: Cheia de acces nu este salvata in codul sursa de pe GitHub, ci este configurata securizat prin variabila de mediu `STEAM_API_KEY` (in sectiunea Environment pe Render).

---

Autentificare Securizata prin Steam (OpenID 2.0) & Sistem de Abonamente

Pentru a garanta ca doar detinatorul real al unui cont Steam se poate autentifica, platforma integreaza protocolul oficial Steam OpenID 2.0 (similar cu Leetify / CSStats):

Conectare prin Steam (`GET /auth/steam` & `GET /auth/steam/callback`):
  Utilizatorul este redirectionat pe pagina oficiala Steam, iar serverul verifica criptografic semnatura primita (`check_authentication` -> `is_valid:true`).
  La prima conectare se creeaza automat un cont cu rolul Standard si un profil de jucator asociat.
  Import & sincronizare automata: La fiecare autentificare prin Steam, aplicatia preia si actualizeaza automat Nickname-ul, Avatarul si statisticile CS2 (`Kills`, `Deaths`, `ADR`, `HS%`) daca profilul are Game Details pe Public.
Upgrade la Premium (`POST /me/upgrade`):
  Utilizatorii logati cu rol Standard au acces la butonul Upgrade Premium (1 EUR/luna) din bara de navigare (simulare subscriptie), care le actualizeaza rolul in baza de date si emite un nou token JWT cu drepturi Premium.
Beneficii & Transparenta Cont Premium:
  Editare profil propriu (`PUT /me/profile`): Conturile Premium/Admin isi pot actualiza nickname-ul din platforma.
  Marcare date manuale (`is_manual`): Jucatorii adaugati manual de un cont Premium sunt marcati automat in baza de date si afisati in Player Dashboard cu avertismentul **`Adaugat manual (Statistici neverificate)`.
Administrare Conturi & Downgrade (`GET /account-badges`, `POST /admin/downgrade/{user_id}`):
  Player Dashboard afiseaza badge-ul tipului de cont asociat fiecarui jucator (Standard / Premium).
  Contul de Admin poate retrograda oricand un utilizator Premium inapoi la Standard direct din interfata, printr-un singur click.
  onturile rapide de demonstratie (Admin, Premium, Standard) raman disponibile in fereastra de autentificare pentru testare rapida.

---

 Imbunatatiri Performanta & Securitate Interfata

Suport flexibil linkuri Steam (`ResolveVanityURL`): Functia de import din Steam Web API accepta atat SteamID64, cat si linkuri complete de profil (`/profiles/7656...`) sau linkuri personalizate (`/id/nume/`).
Load Test direct din Browser: In panoul de Etapa 4 a fost adaugat butonul Ruleaza Load Test (50 Cereri) care trimite cereri concurente (10 utilizatori simultani) catre `/players` direct din browser (util pentru demonstratii live pe Render, fara terminal), afisand rata de succes, throughput-ul (`req/s`) si latentele (`min`, `medie`, `max`).
Restrictionare UI pentru Admin: Intregul panou de Etapa 4 (generator boti, benchmark indici SQL, stergere boti si Load Test) este vizibil exclusiv utilizatorilor autentificati cu rolul Admin.