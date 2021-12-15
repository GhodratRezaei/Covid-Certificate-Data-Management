from flask import Blueprint, render_template, redirect, url_for, request

from datetime import timedelta, datetime

from covidapp.extensions import mongo

main = Blueprint('main', __name__)

auth_bodies_ids = {'Milano Hospital': 1, 'Turin Hospital': 2, 'Lecco Hospital': 3, 'Como Laboratory': 4}

def make_html_table(obj):
    if isinstance(obj, list) and len(obj) > 0:
        html = "<table>\n"
        html += "<tr>\n"
        for f in obj[0]:
            html += "<th>"+f+"</th>\n"
        html += "</tr>\n"
        for f in obj:
            html += "<tr>"+make_html_table(f)+"</tr>\n"
        html += "</table>\n"
        return html
    elif isinstance(obj, dict) and len(obj) > 0:
        # html = "<table>\n"
        # html += "<tr>\n"
        # for f in obj:
        #     html += "<th>"+f+"</th>\n"
        # html += "</tr>\n"
        html = "<tr>\n"
        for f in obj:
            html += make_html_table(obj[f])
        html += "</tr>\n"
        # html += "</tr></table>\n"
        return html
    else:
        return "<td>"+str(obj)+"</td>\n"

def dummy():
    return "hello"

@main.route('/', methods=['GET'])
def index(data=''):
    return render_template('index.html', data=data)

@main.route('/find_person_emergency_contact', methods=['POST'])
def find_person_emergency_contact():
    collection  = mongo.db.People
    person_name = request.form.get('person-name')
    try:
        result = collection.find_one({'Name':person_name}, {'EmergencyContactInfo':1,'_id':0})
    except Exception:
        result = [{'Message': str(Exception)}]
        return render_template('index.html', data=make_html_table(result))
    if result != None:
        result = [result['EmergencyContactInfo']]
    else:
        result = [{'Message': 'Person not found.'}]
    return render_template('index.html', data=make_html_table(result))

@main.route('/vaccination_percentage', methods=['POST'])
def vaccination_percentage():
    collection  = mongo.db.People
    try:
        brands = collection.aggregate([{
            '$group': {
                '_id': '$Vaccines.Brand',
                'num': {'$sum': 1}
            },
        }])
    except Exception:
        result = [{'Message': str(Exception)}]
    brand_usage={}
    total = 0
    print('*', brands)
    for brand in brands:
        print('\t', brand)
        for brandname in brand['_id']:
            print('\t\t', brandname)
            if brandname not in brand_usage.keys():
                brand_usage[brandname] = brand['num']
            else:
                brand_usage[brandname] += brand['num']
            total += brand['num']
    for brand in brand_usage:
        brand_usage[brand] = round((brand_usage[brand] / total) * 100, 2)
        print('\t', brand, brand_usage[brand])
    
    selected = request.form.get("vaccine-brand")
    if selected != "All":
        brand_usage = {selected: brand_usage[selected]}
    brand_usage = [brand_usage]
    return render_template('index.html', data=make_html_table(brand_usage))

@main.route('/authorized_body_type_count', methods=['POST'])
def authorized_body_type_count():
    collection = mongo.db.AuthorizedBodies
    authorized_body_type = request.form.get('authorized-body-type')
    result = collection.count_documents({
                        'Type': authorized_body_type
    })
    result = [{'# of authorized bodies of type '+authorized_body_type: result}]
    return render_template('index.html', data=make_html_table(result))

@main.route('/list_of_vaccinations_per_authorized_body', methods=['POST'])
def list_of_vaccinations_per_authorized_body():
    collection = mongo.db.AuthorizedBodies
    authorized_body_name = request.form.get('authorized-body-name')
    authorized_body_id = collection.find_one({'Name':authorized_body_name},{'_id':1})
    if (authorized_body_id == None):
        result = [{'Message': 'No records found'}]
    else:
        collection = mongo.db.People
        result = collection.find({'Vaccines.Auth':authorized_body_id['_id']},{'Name':1})
        result = [r for r in result]
    
    return render_template('index.html', data=make_html_table(result))

@main.route('/check_vaccine_validity', methods=['POST'])
def check_vaccine_validity():
    collection = mongo.db.People
    person_name = request.form.get('person-name')
    person = collection.find_one({'Name': person_name}, {'Vaccines': 1})
    if (person == None):
        message = 'Person not found.'
    elif len(person['Vaccines'])==0:
        message = 'This person is not vaccinated.'
    else:
        vaccines = person['Vaccines']
        last_dose_injection_date = vaccines[-1]['InjectionDate']
        if not isinstance(last_dose_injection_date, datetime):
            last_dose_injection_date = datetime.strptime(vaccines[-1]['InjectionDate'], '%Y-%m-%d')
        last_dose_brand = vaccines[-1]['Brand']
        last_dose_number = len(vaccines)
        collection = mongo.db.Validities
        ValidityTime = collection.find_one({
                    'Brand': last_dose_brand},
                    {'Validity': 1
            })['Validity'][last_dose_number - 1]
        validityOfInjection = last_dose_injection_date + timedelta(days=30 * ValidityTime)
        if validityOfInjection < datetime.now():
            message = 'The vaccination has expired on {}'.format(validityOfInjection.date())
        else:
            message = 'The vaccination is valid until {}'.format(validityOfInjection.date())
    result = [{'Message': message}]
    return render_template('index.html', data=make_html_table(result))

@main.route('/add_person', methods=['POST'])
def add_person():
    collection  = mongo.db.People
    person_name = request.form.get('person-name')
    phone_num = request.form.get('phone-number')
    emergency_name = request.form.get('emergency-contact-name')
    emergency_num = request.form.get('emergency-contact-phone-number')
    insert_result = collection.insert_one({'Name': person_name, 
                            'Vaccines':[],
                            'Tests':[],
                            'ContactInfo':phone_num,
                            'EmergencyContactInfo':{
                            'Name':emergency_name,
                            'ContactInfo':emergency_num
                             }})
    print(insert_result)
    result = [{'Message': 'Operation successful.'}]
    return render_template('index.html', data=make_html_table(result))

@main.route('/add_vaccine_record', methods=['POST'])
def add_vaccine_record():
    collection = mongo.db.People
    person_name = request.form.get('person-name')
    vaccination_place = request.form.get('vaccination-place')
    vaccine_brand = request.form.get('vaccine-brand')
    authorized_body_name = request.form.get('authorized-body-name')
    vaccine_type = request.form.get('vaccine-type')
    vaccine_lot = request.form.get('vaccine-lot')
    production_date = datetime.strptime(request.form.get('production-date'), '%Y-%m-%d')
    injection_date = datetime.strptime(request.form.get('injection-date'), '%Y-%m-%d')
    injecting_nurse_doctor = request.form.get('injecting-nurse-doctor')
    update_result = collection.update_one({'Name':person_name},
                            {'$push':{'Vaccines':
                                        {'Place':vaccination_place,
                                        'Brand':vaccine_brand,
                                        'Type':vaccine_type,
                                        'lot':vaccine_lot,
                                        'PDate': production_date,
                                        'InjectionDate': injection_date,
                                        'D/N': injecting_nurse_doctor,
                                        'Auth': auth_bodies_ids[authorized_body_name]
                                            }}})
    result = [{'Message': str(update_result.modified_count)+' documents modified.'}]
    return render_template('index.html', data=make_html_table(result))

@main.route('/add_test_record', methods=['POST'])
def add_test_record():
    collection = mongo.db.People
    person_name = request.form.get('person-name')
    test_place = request.form.get('test-place')
    test_result = request.form.get('test-result')
    test_date = request.form.get('test-date')
    doctor_nurse_name = request.form.get('doctor-nurse-name')
    update_result = collection.update_one({'Name':person_name},
                            {'$push':{'Tests':
                                          {'Result':test_result,
                                           'Date':test_date,
                                           'Place': test_place,
                                           'D/N':doctor_nurse_name}}})
    result = [{'Message': str(update_result.modified_count)+' documents modified.'}]
    return render_template('index.html', data=make_html_table(result))