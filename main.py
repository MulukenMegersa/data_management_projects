import pandas as pd
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By

HOMEPAGE = "https://www.cognomix.it/origine-cognomi-italiani/A"

letters = [
    {"letter": 'A', "size": 14},
    {"letter": 'B', "size": 24},
    {"letter": 'C', "size": 28},
    {"letter": 'D', "size": 16},
    {"letter": 'E', "size": 2},
    {"letter": 'F', "size": 12},
    {"letter": 'G', "size": 15},
    {"letter": 'I', "size": 4},
    {"letter": 'L', "size": 10},
    {"letter": 'M', "size": 20},
    {"letter": 'N', "size": 4},
    {"letter": 'O', "size": 3},
    {"letter": 'P', "size": 19},
    {"letter": 'Q', "size": 1},
    {"letter": 'R', "size": 9},
    {"letter": 'S', "size": 19},
    {"letter": 'T', "size": 10},
    {"letter": 'U', "size": 1},
    {"letter": 'V', "size": 7},
    {"letter": 'Z', "size": 5}
]

data = []


def get_data(url):
    browser_options = ChromeOptions()
    driver = Chrome(options=browser_options)
    driver.get(url)

    list_element = driver.find_elements(By.XPATH, '//ul/li/a[contains(@href, "cognomix.it/origine-cognome/")]')

    for item in list_element:
        name = item.text.split("-")[0]
        data.append({'name': name})
        print(name)

    driver.quit()
    return data


def export_csv(data):
    df = pd.DataFrame(data)
    # Apply transformations if needed
    df.to_csv("books_exported.csv", index=False)
    print(df)  # DEBUG


def main():
    for list in letters:
        print(list["letter"], list["size"])
        for i in range(1, list["size"] + 1):
            new_url = f"https://www.cognomix.it/origine-cognomi-italiani/{list['letter']}/{i}"
            get_data(url=new_url)
    export_csv(data)
    print('DONE')


if __name__ == '__main__':
    main()
