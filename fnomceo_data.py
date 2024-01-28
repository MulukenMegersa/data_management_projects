import json
import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

file_path = 'surename.csv'

HOMEPAGE = "https://portale.fnomceo.it/cerca-prof/index.php"

data = []


def get_data(url, df):
    browser_options = ChromeOptions()
    driver = Chrome(options=browser_options)
    driver.get(url)

    wait = WebDriverWait(driver, 10)

    for outer_index, row in df.iterrows():
        sure_name_input = row["name"]

        sure_name = wait.until(EC.presence_of_element_located((By.ID, "cognomeID")))

        # sure_name = driver.find_element(By.ID, "cognomeID")
        search = driver.find_element(By.ID, "submitButtonID")

        sure_name.send_keys(sure_name_input)

        search.click()

        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete')

        table_data = driver.execute_script("""
        var table = $('#dataTableID').DataTable();
        var data = table.rows().data();
        return  JSON.stringify(data);
        """)

        parsed_data = json.loads(table_data)

        del parsed_data["context"]
        del parsed_data["selector"]
        del parsed_data["length"]
        del parsed_data["ajax"]

        keys_list = list(parsed_data.keys())

        for index in keys_list:
            user = {}
            selected_row = parsed_data[index]
            selected_row_id = selected_row[0]

            user["person_id"] = selected_row_id
            user["surname"] = selected_row[1]
            user["first_name"] = selected_row[2]

            parts = selected_row[3].split()
            user["date_of_birth"] = parts[0]
            user['birth_place'] = ' '.join(parts[1:])

            user["province"] = selected_row[4].split("Ordine della Provincia di")[1]

            script = "return await $.post('https://portale.fnomceo.it/cerca-prof/dettaglio.php', {{id: {}}})".format(
                selected_row_id)

            data_internal_html = driver.execute_script(script);
            soup = BeautifulSoup(data_internal_html, 'html.parser')
            soup_full_name = soup.find('h4', class_='modal-title text-uppercase d-print-block')

            if soup_full_name:
                extracted_full_name = soup_full_name.getText(strip=True)
                user["full_name"] = extracted_full_name
                user["prefix"] = extracted_full_name.split(" ")[0]

            mult_iscrizioni = []
            mult_lauree = []
            mult_abilitazioni = []
            mult_specializzazioni = []
            mult_elenchi_speciali = []
            ul_element = soup.find('ul', class_="list-group")
            if ul_element:
                for li_element in ul_element.find_all('li'):
                    li_text_value = li_element.get_text(strip=True)
                    li_name = li_element.find('span', class_='badge').get_text(strip=True)
                    li_text_value = li_text_value.replace(li_name, "")
                    formatted_value = re.sub(' +', ' ', li_text_value)
                    if li_name:
                        if li_name == "iscrizioni":
                            iscrizioni_data = {}
                            registrations = formatted_value.replace("\"", "").replace("'", "").split(" - ")
                            registration_year = registrations[0].split(" ")[-1]
                            # prop = registrations[1].split("Albo Provinciale dei Medici Chirurghi di")[1]
                            pattern = r'Ordine della Provincia di (\S+)'
                            match = re.search(pattern, formatted_value)
                            if match:
                                registration_province = match.group(1).replace(")", "")
                            second_prop = formatted_value.split("(")
                            registration_number = ''.join(re.findall(r'\d', second_prop[1]))
                            iscrizioni_data["province"] = registration_province
                            iscrizioni_data["year"] = registration_year
                            iscrizioni_data["number"] = registration_number
                            mult_iscrizioni.append(iscrizioni_data)
                        elif li_name == "lauree":
                            lauree_data = {}
                            degree = formatted_value.replace("\"", "").replace("'", "").split(" - ")
                            degree_year = degree[0].split(" ")[-1]
                            degree_name_with_uni = degree[1]
                            pattern = r'\((.*?)\)'
                            match = re.search(pattern, degree_name_with_uni)
                            if match:
                                lauree_data["university_name"] = match.group(1)
                            lauree_name = degree_name_with_uni.split("(")[0]
                            lauree_data["name"] = lauree_name
                            lauree_data["year"] = degree_year
                            mult_lauree.append(lauree_data)
                        elif li_name == "abilitazioni":
                            abilitazioni_data = {}
                            qualification = formatted_value.replace("\"", "").replace("'", "").split(" - ")
                            qualification_data = qualification[0].split("/")
                            qualification_year = qualification_data[0]
                            qualification_round = qualification_data[1]
                            qualification_name_with_uni = qualification[1]
                            pattern = r'\((.*?)\)'
                            match = re.search(pattern, qualification_name_with_uni)
                            if match:
                                abilitazioni_data["university_name"] = match.group(1)
                            qualification_name = qualification_name_with_uni.split("(")[0]
                            abilitazioni_data["name"] = qualification_name
                            abilitazioni_data["year"] = qualification_year
                            abilitazioni_data["round"] = qualification_round
                            mult_abilitazioni.append(abilitazioni_data)
                        elif li_name == "specializzazioni":
                            specializzazioni_data = {}
                            specializzazioni = formatted_value.replace("\"", "").replace("'", "").split(" - ")
                            specializzazione_year = specializzazioni[0].split(" ")[-1]
                            specializzazione_name_with_uni = specializzazioni[1]
                            pattern = r'\((.*?)\)'
                            match = re.search(pattern, specializzazione_name_with_uni)
                            if match:
                                specializzazioni_data["university_name"] = match.group(1)
                            specializzazione_name = specializzazione_name_with_uni.split("(")[0]
                            specializzazioni_data["specializzazione_name"] = specializzazione_name
                            specializzazioni_data["year"] = specializzazione_year
                            mult_specializzazioni.append(specializzazioni_data)
                        elif li_name == "elenchi speciali":
                            mult_elenchi_data = {}
                            name = formatted_value.split("TITOLO FORMAZIONE ")[-1]
                            mult_elenchi_data[name] = name
                            mult_elenchi_speciali.append(mult_elenchi_data)

                        if mult_iscrizioni:
                            user["iscrizioni"] = mult_iscrizioni
                        if mult_lauree:
                            user["lauree"] = mult_lauree
                        if mult_abilitazioni:
                            user["abilitazioni"] = mult_abilitazioni
                        if mult_specializzazioni:
                            user["specializzazioni"] = mult_specializzazioni
                        if mult_elenchi_speciali:
                            user["elenchi_speciali"] = mult_elenchi_speciali

            last_updated = soup.find('p', class_="small text-muted")
            if last_updated:
                user['last_update_date'] = last_updated.text.split("Data aggiornamento: ")[1]

            if user:
                data.append(user)

            # back_link = driver.find_element(By.XPATH, "/html/body/div[4]/div[1]/div/nav/a[1]")

            # back_link.click()
        print(f"Index: {outer_index} Name:{sure_name_input} Total_Data: {len(data)}")

        if len(data) >= 10000:
            break

        try:
            back_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='nav-link' and text()='Nuova ricerca']")))

            driver.execute_script("arguments[0].click();", back_link)
        except Exception as e:
            print(f"Error: {e}")




def export_csv(output):
    df = pd.DataFrame(output)
    df.to_csv("main_data.csv", index=False)
    print(df)


def main():
    start_time = time.time()
    df = pd.read_csv(file_path)
    get_data(url=HOMEPAGE, df=df)
    export_csv(data)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"DONE Total time taken: {total_time} seconds")


if __name__ == '__main__':
    main()
