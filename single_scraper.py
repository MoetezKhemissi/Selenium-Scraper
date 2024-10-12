import json
import csv
import re  # Added import for regular expressions
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

    # Extract Likes and Dislikes
    try:
        # Likes
        likes_element = driver.find_element(
            By.XPATH, "//button[@aria-label='like']//div[contains(@class, 'counter')]"
        )
        likes_text = likes_element.text.strip()
        problem_data['likes'] = parse_numeric_value(likes_text)

        # Dislikes
        dislikes_element = driver.find_element(
            By.XPATH, "//button[@aria-label='dislike']//div[contains(@class, 'counter')]"
        )
        dislikes_text = dislikes_element.text.strip()
        problem_data['dislikes'] = parse_numeric_value(dislikes_text)
    except Exception as e:
        print(f"Error extracting likes/dislikes from {problem_url}: {e}")
        problem_data['likes'] = problem_data['dislikes'] = None

    # Extract Description
    try:
        description_element = driver.find_element(
            By.XPATH, "//div[@data-track-load='description_content']"
        )
        problem_data['description'] = description_element.text.strip()
    except Exception as e:
        print(f"Error extracting description from {problem_url}: {e}")
        description_element = None
        problem_data['description'] = None

    # Extract Examples and Constraints from the description
    try:
        if description_element:
            description_html = description_element.get_attribute('innerHTML')

            # Use regular expressions to extract examples and constraints
            examples = []
            constraints = []

            # Extract examples
            example_matches = re.findall(
                r'<strong[^>]*class="[^"]*example[^"]*"[^>]*>Example.*?</pre>',
                description_html,
                re.DOTALL | re.IGNORECASE
            )
            for match in example_matches:
                example_text = re.sub(r'<.*?>', '', match)  # Remove HTML tags
                examples.append(example_text.strip())

            # Extract constraints
            constraints_match = re.search(
                r'<strong[^>]*>Constraints:</strong>(.*?)</ul>',
                description_html,
                re.DOTALL | re.IGNORECASE
            )
            if constraints_match:
                constraints_html = constraints_match.group(1)
                constraint_items = re.findall(r'<li>(.*?)</li>', constraints_html)
                constraints = [re.sub(r'<.*?>', '', item).strip() for item in constraint_items]
                problem_data['constraints'] = constraints
            else:
                problem_data['constraints'] = []

            problem_data['examples'] = examples
        else:
            problem_data['examples'] = []
            problem_data['constraints'] = []
    except Exception as e:
        print(f"Error extracting examples and constraints from {problem_url}: {e}")
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

    # Extract Similar Questions
    try:
        similar_questions = extract_similar_questions(driver)
        problem_data['similarQuestions'] = similar_questions
    except Exception as e:
        print(f"Error extracting similar questions from {problem_url}: {e}")
        problem_data['similarQuestions'] = []

    # Print the extracted data before writing to CSV
    print(json.dumps(problem_data, indent=4, ensure_ascii=False))
    
    return problem_data

def extract_hints(driver):
    hints = []
    try:
        # Find all hint labels and their parent with class 'flex-col'
        hint_labels = driver.find_elements(
            By.XPATH, "//div[contains(@class, 'text-body') and starts-with(text(), 'Hint')]"
        )
        
        for label in hint_labels:
            try:
                print(label.text.strip())
                # Get the parent div with class 'flex-col'
                parent_div = label.find_element(By.XPATH, "./ancestor::div[8]")
                print("found",parent_div)
                child_divs = parent_div.find_elements(By.XPATH, ".//div")

                # Print the number of child div elements
                print(f"Number of child divs in parent div: {len(child_divs)}")
                # Now get the text from the sibling div with class 'text-body'
                hint_content_div = parent_div.find_elements(
                    By.XPATH, ".//div[contains(@class, 'text-body') and contains(@class, 'text-sd-foreground')]"
                )
                for hint in hint_content_div:
                    print(hint)
                    hint_content=hint.text.strip()
                    
                    hints.append(hint_content)
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



def save_to_csv(data_list, filename='problems.csv'):
    # Define CSV columns
    columns = ['id', 'title', 'difficulty', 'acceptance', 'likes', 'dislikes', 'description', 'examples', 'constraints', 'hints', 'topics', 'similarQuestions']

    # Open CSV file for writing
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)

        # Write header
        writer.writeheader()

        for data in data_list:
            # Convert lists/dicts to JSON strings
            data['examples'] = json.dumps(data.get('examples', []), ensure_ascii=False)
            data['constraints'] = json.dumps(data.get('constraints', []), ensure_ascii=False)
            data['hints'] = json.dumps(data.get('hints', []), ensure_ascii=False)
            data['topics'] = json.dumps(data.get('topics', []), ensure_ascii=False)
            data['similarQuestions'] = json.dumps(data.get('similarQuestions', []), ensure_ascii=False)

            writer.writerow(data)

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
        save_to_csv(all_problem_data)
        print(f"\nData extraction complete. Saved to 'problems.csv'.")

    except KeyboardInterrupt:
        print("\nScript interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()
