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
