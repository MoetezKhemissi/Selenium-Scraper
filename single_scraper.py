import json
import csv
import re  # Added import for regular expressions
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def parse_numeric_value(text):
    """
    Parses a numeric value that may contain 'K' for thousands or '.' for decimals.
    Returns an integer.
    """
    try:
        text = text.replace(',', '').strip()
        if 'K' in text:
            return int(float(text.replace('K', '')) * 1000)
        elif '.' in text:
            return int(float(text))
        else:
            return int(text)
    except:
        return None

def format_examples(examples):
    """
    Converts extracted examples into the desired structured format with 'input', 'output', and 'explanation'.
    """
    formatted_examples = []
    for example in examples:
        # Split the example based on known structure (Input, Output, and Explanation parts)
        input_match = re.search(r"Input:\s*(.*?)\s*(Output:|$)", example, re.DOTALL)
        output_match = re.search(r"Output:\s*(.*?)\s*(Explanation:|$)", example, re.DOTALL)
        explanation_match = re.search(r"Explanation:\s*(.*)", example, re.DOTALL)

        # Extract and strip the text for input, output, and explanation
        input_example = input_match.group(1).strip() if input_match else ''
        output_example = output_match.group(1).strip() if output_match else ''
        explanation_example = explanation_match.group(1).strip() if explanation_match else ''

        formatted_example = {
            'input': input_example,
            'output': output_example,
            'explanation': explanation_example
        }
        formatted_examples.append(formatted_example)

    return formatted_examples

def extract_problem_data(driver, problem_url):
    # Navigate to the problem page
    driver.get(problem_url)
    
    # Initialize explicit wait
    wait = WebDriverWait(driver, 10)
    
    # Data dictionary to store problem details
    problem_data = {}

    # Extract problem ID and Title
    try:
        title_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class,'text-title-large')]//a")
        ))
        title_text = title_element.text.strip()
        # Split the title to get ID and Title
        id_title = title_text.split('. ', 1)
        problem_data['id'] = int(id_title[0])
        problem_data['title'] = id_title[1]
    except Exception as e:
        print(f"Error extracting title from {problem_url}: {e}")
        return None

    # Extract Difficulty
    try:
        difficulty_element = driver.find_element(
            By.XPATH, "//div[contains(@class,'text-difficulty')]"
        )
        problem_data['difficulty'] = difficulty_element.text.strip()
    except Exception as e:
        print(f"Error extracting difficulty from {problem_url}: {e}")
        problem_data['difficulty'] = None

    # Extract Acceptance Rate
    try:
        acceptance_element = driver.find_element(
            By.XPATH, "//div[contains(text(),'Acceptance Rate')]/following-sibling::div"
        )
        problem_data['acceptance'] = acceptance_element.text.strip()
    except Exception as e:
        print(f"Error extracting acceptance rate from {problem_url}: {e}")
        problem_data['acceptance'] = None

    # Extract Description, Examples, and Constraints
    try:
        description_element = driver.find_element(
            By.XPATH, "//div[@data-track-load='description_content']"
        )
        description_text = description_element.text.strip()
    except Exception as e:
        print(f"Error extracting description from {problem_url}: {e}")
        description_text = ''

    # Extract Examples and Constraints from the description
    try:
        if description_text:
            # Use regular expressions to extract examples and constraints
            examples = []
            constraints = []

            # Extract examples from description_text
            # Regex to find "Example X:" followed by content
            example_pattern = r'(Example \d+:.*?)(?=Example \d+:|Constraints:|$)'
            example_matches = re.findall(example_pattern, description_text, re.DOTALL)

            # Remove examples from description_text
            description_text_no_examples = re.sub(example_pattern, '', description_text, flags=re.DOTALL).strip()

            # Now extract constraints from description_text_no_examples
            constraints_pattern = r'Constraints:\s*(.*)'
            constraints_match = re.search(constraints_pattern, description_text_no_examples, re.DOTALL)

            if constraints_match:
                constraints_text = constraints_match.group(1).strip()
                # Remove constraints from description
                description_text_clean = re.sub(constraints_pattern, '', description_text_no_examples, flags=re.DOTALL).strip()
                # Now process constraints_text to extract individual constraints
                constraints_list = constraints_text.split('\n')
                constraints_list = [constraint.strip() for constraint in constraints_list if constraint.strip()]
                problem_data['constraints'] = constraints_list
            else:
                description_text_clean = description_text_no_examples
                problem_data['constraints'] = []

            # Assign cleaned description to problem_data['description']
            problem_data['description'] = description_text_clean

            # Process examples to desired format
            formatted_examples = []
            for example_text in example_matches:
                # Use regex to extract input, output, explanation
                input_match = re.search(r'Input:\s*(.*?)\s*(Output:|$)', example_text, re.DOTALL)
                output_match = re.search(r'Output:\s*(.*?)\s*(Explanation:|$)', example_text, re.DOTALL)
                explanation_match = re.search(r'Explanation:\s*(.*)', example_text, re.DOTALL)

                # Extract and strip the text for input, output, and explanation
                input_example = input_match.group(1).strip() if input_match else ''
                output_example = output_match.group(1).strip() if output_match else ''
                explanation_example = explanation_match.group(1).strip() if explanation_match else ''

                formatted_example = {
                    'input': input_example,
                    'output': output_example,
                    'explanation': explanation_example
                }
                formatted_examples.append(formatted_example)

            problem_data['examples'] = formatted_examples
        else:
            problem_data['description'] = ''
            problem_data['examples'] = []
            problem_data['constraints'] = []
    except Exception as e:
        print(f"Error extracting examples and constraints from {problem_url}: {e}")
        problem_data['description'] = ''
        problem_data['examples'] = []
        problem_data['constraints'] = []

    # Extract Hints
    try:
        hints = extract_hints(driver)
        problem_data['hints'] = hints
    except Exception as e:
        print(f"Error extracting hints from {problem_url}: {e}")
        problem_data['hints'] = []

    # Extract Topics
    try:
        topics = extract_topics(driver)
        problem_data['topics'] = topics
    except Exception as e:
        print(f"Error extracting topics from {problem_url}: {e}")
        problem_data['topics'] = []



    # Print the extracted data before writing to CSV
    print(json.dumps(problem_data, indent=4, ensure_ascii=False))
    
    return problem_data

def extract_hints(driver):
    hints = []
    try:
        # Find all hint labels
        hint_labels = driver.find_elements(
            By.XPATH, "//div[contains(@class, 'text-body') and starts-with(text(), 'Hint')]"
        )
        
        for label in hint_labels:
            try:
                label.click()
                time.sleep(2)  

                parent_div = label.find_element(By.XPATH, "./ancestor::div[5]")

                hint_content_divs = parent_div.find_elements(
                    By.XPATH, ".//div[contains(@class, 'text-sd-foreground') and normalize-space(text())]"
                )

                for child_div in hint_content_divs:
                    div_text = child_div.text.strip()

                    if re.match(r"Hint \d+", div_text):
                        continue

                    if div_text:
                        hints.append(div_text)

            except Exception as e:
                print(f"Error extracting hint content: {e}")
                hints.append(None)

        print(f"Extracted Hints: {hints}")  # Debugging statement

    except Exception as e:
        print(f"Error extracting hints: {e}")
    return hints

def extract_similar_questions(driver):
    similar_questions = []
    try:
        # Find the 'Similar Questions' label
        similar_questions_label = driver.find_element(
            By.XPATH, "//div[contains(@class, 'text-body') and text()='Similar Questions']"
        )
        similar_questions_label.click()
        # Find all similar question links
        question_elements = similar_questions_label.find_elements(
            By.XPATH, "following-sibling::div//a"
        )
        for elem in question_elements:
            title = elem.text.strip()
            link = elem.get_attribute('href')
            # Find the difficulty, assuming it's a sibling in the same parent
            try:
                parent = elem.find_element(By.XPATH, "../../div[contains(@class, 'flex-none')]")
                difficulty = parent.text.strip()
            except:
                difficulty = "Unknown"
            similar_questions.append({
                'title': title,
                'difficulty': difficulty,
                'link': link
            })
        print(f"Extracted Similar Questions: {similar_questions}")  # Debugging statement
    except Exception as e:
        print(f"Error extracting similar questions: {e}")
    return similar_questions

def extract_topics(driver):
    topics = []
    try:
        # Wait for all <a> elements with href containing '/tag/'
        wait = WebDriverWait(driver, 10)
        topic_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//a[contains(@href, '/tag/')]")
        ))

        # Extract the topic name from href for each topic
        for elem in topic_elements:
            topic_href = elem.get_attribute('href')  # Extract the href attribute
            # Extract the topic word from the href by splitting the URL
            topic_word = topic_href.split('/')[-2]  # Get the second-to-last part of the URL
            topics.append(topic_word)

        print(f"Extracted Topics: {topics}")  # Debugging statement

    except Exception as e:
        print(f"Error extracting topics: {e}")
    return topics

def save_to_json(data_list, filename='questions_new.json'):
    # Open JSON file for writing
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        # Save the entire data list as JSON
        json.dump(data_list, jsonfile, ensure_ascii=False, indent=4)
def main():
    # Set up options for headless browsing
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    # Uncomment the next line to run Chrome in headless mode
    # options.add_argument("--headless")

    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=options)

    try:
        # List of problem URLs to extract
        with open('problem_links.txt', 'r') as file:
            lines = file.readlines()

        # Extract URLs from the file and store them in a list
        problem_urls = []
        for line in lines:
            line = line.strip()  # Remove leading/trailing whitespaces
            if line:  # Ensure the line is not empty
                print(f"Adding URL: {line}")
                problem_urls.append(line)

        # Display the list of problem URLs
        print(f"\nTotal problems to extract: {len(problem_urls)}")
        all_problem_data = []

        for url in problem_urls:
            print(f"\nExtracting data from: {url}")
            data = extract_problem_data(driver, url)
            if data:
                all_problem_data.append(data)
                print(f"Successfully extracted data for problem ID {data['id']}")
            else:
                print(f"Failed to extract data from {url}")

        # Save the data to CSV
        save_to_json(all_problem_data)
        print(f"\nData extraction complete. Saved to 'questions_new.json'.")

    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()
