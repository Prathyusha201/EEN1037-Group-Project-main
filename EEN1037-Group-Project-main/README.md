# EEN1037-Group-Project

## Authors

* **Oscar Grellan Ganly** - [@oscarganly](https://github.com/oscarganly)
* **Saiteja Botla** - [@Saiteja5757](https://github.com/Saiteja5757)
* **Antoine Lebeault** - [@Theucalyptus](https://github.com/Theucalyptus)
* **Priyanka Bommisetty** - [@priyanka170627](https://github.com/priyanka170627)
* **Keith Molloy** - [@kaymol22](https://github.com/kaymol22)
* **Hamdan Bin Abdul Rahman** - [@hamdanrahman17](https://github.com/hamdanrahman17)
* **Prathyusha Murali Mohan Raju** - [@Prathyusha201](https://github.com/Prathyusha201)
* **Romain Very** - [@RomaiinVery](https://github.com/RomaiinVery)


### API
API Root:
<adress>:<port>/api

#### Authentication
Bassic HTTP Authentication

#### Authorisation
All logged users have read-write access to everything, anonymous users are read-only

#### Endpoints
- /machines/: list all machines (GET only)
- /machines/\<ID\>/: view all info about a machine, identified by its ID, and allows for its status to be changed (GET and PATCH)
- /cases/: list all issues (GET) and create a new case (POST)
- /cases/open/: same as above but with a filter to only display opened issues (GET)
- /cases/\<ID\>/: view all details about a case (GET)
- /cases/\<ID\>/updates/: view the list of all updates associated with a case (GET), and push a new update (POST)  
- /caseupdate/\<ID\>/: view a specific case update

#### Usage Examples
To open a new case, using HTTPie:
`http -a "username":"password" POST localhost:8000/api/cases/ machine="ID" status="Open" description="My description"`

To push a new case:
`http -a "username":"password" POST localhost:8000/api/cases/\<ID\>/updates/ update_text="My update text"`