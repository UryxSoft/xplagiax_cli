
from modules.models.model import Users, Country, Institution

class ComplementsGetter:
    def __init__(self):
        self.params = {}

    def set_param(self, key, value):
        self.params[key] = value

    def get_complements(self):
        results = {}
        
        countryload = Country.query.filter_by(id=self.params.get('country_id')).first()
        results['country_name'] = countryload.country if countryload else "No associated Country loaded"
        
        instituteload = Institution.query.filter_by(id=self.params.get('institute_id')).first()
        results['institute_name'] = instituteload.institution if instituteload else "No associated Institution loaded"
        
        #users = Users.query.filter_by(ID=self.params.get('CREATED_BY_ID')).first()
        #results['users_name'] = users.NAME if users else "No associated USER"
        
        # Filtrar solo los parámetros que fueron introducidos
        filtered_results = {k: v for k, v in results.items() if v is not None}
        
        return filtered_results
