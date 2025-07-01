from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from pandas import DataFrame
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from functools import partial

def search_carrots():
    options = webdriver.ChromeOptions()
    
    # Basic options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Handle WebGL issues
    options.add_argument('--enable-unsafe-swiftshader')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-gpu-sandbox')
    options.add_argument('--disable-features=UseOzonePlatform')
    options.add_argument('--disable-webgl')
    options.add_argument('--disable-webgl2')
    
    # Disable unnecessary features
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    
    # Add stealth options
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Add these options to the ChromeOptions
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.page_load_strategy = 'eager'
    
    try:
        # Initialize WebDriver
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to the page
        search_url = "https://www.carrefouruae.com/mafuae/en/search?keyword=carrots"
        driver.get(search_url)
        
        # Wait for page to load completely
        print("Waiting for page to load completely...")
        time.sleep(5)
        
        # Handle cookie popup
        try:
            wait = WebDriverWait(driver, 10)
            cookie_button = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print("Accepted cookies")
            time.sleep(2)
        except Exception as e:
            print(f"Error handling cookie popup: {e}")
        
        # Add this after the cookie handling (around line 68):
        def click_load_more(driver):
            try:
                # Wait for and find the load more button
                load_more = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((
                        By.XPATH, "//button[contains(text(), 'Load more')]"
                    ))
                )
                
                # Scroll to the button
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
                time.sleep(1)  # Brief pause for stability
                
                # Click the button
                load_more.click()
                time.sleep(2)  # Wait for new products to load
                return True
            except:
                return False
        
        # Then modify the product search section (around line 71-85) to:
        try:
            print("Waiting for products to load...")
            wait = WebDriverWait(driver, 20)
            
            # Wait for the product grid to load
            product_grid = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                "div.relative.flex.overflow-hidden.rounded-xl"
            )))
            
            # Click load more until no more products
            while click_load_more(driver):
                print("Clicked load more, waiting for products...")
                time.sleep(2)
            
            print("No more products to load")
            
            # Find all product cards
            products = driver.find_elements(By.CSS_SELECTOR, "div.relative")
            print(f"Found {len(products)} total products")

            # Initialize lists (not sets) to store data
            product_data = {
                'Name': [],
                'Price': [],
                'Quantity': [],
                'Origin': []
            }

            for product in products:
                try:
                    # Get the HTML of the product to inspect structure
                    html = product.get_attribute('outerHTML')
                    if 'carrot' in html.lower():  # Only process elements that might be carrot products
                        print("\nFound potential carrot product:")
                        
                        # Try multiple selectors for the name
                        name_selectors = [
                            "span",  # Most basic
                            "div[class*='line-clamp'] span",
                            "div[class*='text-sm'] span",
                            "a span"
                        ]
                        
                        name = None
                        for selector in name_selectors:
                            try:
                                name_elem = product.find_element(By.CSS_SELECTOR, selector)
                                if name_elem and 'carrot' in name_elem.text.lower():
                                    name = name_elem.text.strip()
                                    break
                            except:
                                continue
                        
                        if name:
                            print(f"Name: {name}")
                            
                            # Try to get price (looking for number followed by AED)
                            try:
                                # Find the price container with the flex layout
                                price_container = product.find_element(By.CSS_SELECTOR, "div.flex.items-center")
                                
                                # Get the main number and decimal parts separately
                                main_number = price_container.find_element(
                                    By.CSS_SELECTOR, 
                                    "div.text-lg.leading-5.font-bold.md\\:text-2xl"
                                ).text.strip()
                                
                                # Get the decimal container
                                decimal_container = price_container.find_element(
                                    By.CSS_SELECTOR, 
                                    "div.ml-px.flex.flex-col"
                                )
                                
                                # Get the decimal number
                                decimal_number = decimal_container.find_element(
                                    By.CSS_SELECTOR, 
                                    "div.text-2xs.font-bold.leading-\\[10px\\]"
                                ).text.strip()
                                
                                # Remove any non-numeric characters
                                main_number = ''.join(filter(str.isdigit, main_number))
                                decimal_number = ''.join(filter(str.isdigit, decimal_number))
                                
                                # Combine them properly
                                price = f"{main_number}.{decimal_number}"
                                print(f"Price: {price} AED")
                            except Exception as e:
                                print(f"Error in price extraction: {e}")
                                # Print the HTML for debugging
                                try:
                                    print("Price container HTML:")
                                    price_html = product.find_element(By.CSS_SELECTOR, "div.flex.items-center").get_attribute('outerHTML')
                                    print(price_html)
                                except:
                                    print("Could not get price container HTML")
                            
                            # Try to get quantity
                            try:
                                quantity_selectors = [
                                    "div[class*='text-gray']",
                                    "div[class*='truncate']",
                                    "div[class*='text-sm']"
                                ]
                                
                                for selector in quantity_selectors:
                                    quantity_elem = product.find_element(By.CSS_SELECTOR, selector)
                                    if quantity_elem and any(unit in quantity_elem.text.lower() for unit in ['kg', 'g', 'piece']):
                                        print(f"Quantity: {quantity_elem.text}")
                                        break
                            except Exception as e:
                                print(f"Error extracting quantity: {e}")
                            
                            # Try to get the product link
                            try:
                                product_link = product.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
                                if product_link:
                                    # Store current window handle
                                    main_window = driver.current_window_handle
                                    
                                    # Open link in new tab
                                    driver.execute_script(f"window.open('{product_link}', '_blank');")
                                    
                                    # Switch to new tab
                                    new_window = driver.window_handles[-1]
                                    driver.switch_to.window(new_window)
                                    
                                    # Wait for origin element to load
                                    wait = WebDriverWait(driver, 10)
                                    print(f"\nDebug: Current product page URL: {driver.current_url}")

                                    # Wait for page load
                                    time.sleep(3)

                                    # Get and save the product page HTML for inspection
                                    print("\nDebug: Saving product page HTML...")
                                    with open("product_page.html", "w", encoding="utf-8") as f:
                                        f.write(driver.page_source)
                                    print("Saved product page HTML to product_page.html")

                                    # Try to find any elements containing 'Origin'
                                    print("\nDebug: Looking for elements containing 'Origin'...")
                                    origin_containing_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Origin')]")
                                    for elem in origin_containing_elements:
                                        print("\nFound element containing 'Origin':")
                                        print("Tag:", elem.tag_name)
                                        print("Class:", elem.get_attribute('class'))
                                        print("Text:", elem.text)
                                        print("Parent HTML:", elem.find_element(By.XPATH, "..").get_attribute('outerHTML'))

                                    # Replace the origin selectors with:
                                    origin_selectors = [
                                        # Look for the specific div class containing Origin
                                        "//div[contains(@class, 'css-p1qrqm')]",
                                        # Look for any element containing Origin text
                                        "//*[contains(text(), 'Origin')]",
                                        # Try finding the specific product info section
                                        "//div[contains(@class, 'product-info')]//div[contains(text(), 'Origin')]",
                                        # Look for any text containing Origin
                                        "//*[text()='Origin -']/following-sibling::*",
                                        # Try finding the specific structure
                                        "//div[contains(@class, 'css-')]//div[text()='Origin -']/following-sibling::div"
                                    ]

                                    print("\nDebug: Starting origin extraction...")
                                    origin_text = "N/A"
                                    for selector in origin_selectors:
                                        try:
                                            print(f"\nTrying selector: {selector}")
                                            elements = driver.find_elements(By.XPATH, selector)
                                            if elements:
                                                print(f"Found {len(elements)} matching elements")
                                                for elem in elements:
                                                    text = elem.text.strip()
                                                    print(f"Element text: '{text}'")
                                                    print(f"Element HTML: {elem.get_attribute('outerHTML')}")
                                                    
                                                    if text and text != "-":
                                                        # Get the parent element to check for sibling text
                                                        parent = elem.find_element(By.XPATH, "..")
                                                        parent_html = parent.get_attribute('outerHTML')
                                                        print(f"Parent HTML: {parent_html}")
                                                        
                                                        # Try to find origin text in parent's children
                                                        siblings = parent.find_elements(By.XPATH, "./div")
                                                        for sibling in siblings:
                                                            sibling_text = sibling.text.strip()
                                                            if sibling_text and sibling_text != "Origin -":
                                                                origin_text = sibling_text
                                                                print(f"Found origin in sibling: {origin_text}")
                                                                break
                                                        
                                                        if origin_text == "N/A" and 'Origin' in text:
                                                            # Try to get text after "Origin -"
                                                            parts = text.split('Origin -')
                                                            if len(parts) > 1:
                                                                origin_text = parts[1].strip()
                                                                print(f"Found origin in text split: {origin_text}")
                                                                break
                                                    
                                                    if origin_text != "N/A":
                                                        break
                                                if origin_text != "N/A":
                                                    break
                                        except Exception as e:
                                            print(f"Error with selector {selector}: {e}")

                                    if origin_text == "N/A":
                                        # Try one final direct approach
                                        try:
                                            location_div = driver.find_element(By.XPATH, "//div[contains(@class, 'location-icon')]/..")
                                            if location_div:
                                                print("\nFound location container:")
                                                print(f"Container HTML: {location_div.get_attribute('outerHTML')}")
                                                text = location_div.text.strip()
                                                if 'Origin' in text:
                                                    origin_text = text.split('Origin -')[-1].strip()
                                                    print(f"Found origin through container: {origin_text}")
                                        except Exception as e:
                                            print(f"Error in final attempt: {e}")

                                    print(f"\nFinal origin result: {origin_text}")
                                    
                                    # Close tab and switch back
                                    driver.close()
                                    driver.switch_to.window(main_window)
                                    
                            except Exception as e:
                                origin_text = "N/A"
                                print(f"Error getting origin: {e}")
                            
                            print("-" * 50)
                
                            if name and price:  # Only add if we have at least name and price
                                # Clean the data
                                name = name.strip()
                                price = price.strip()
                                
                                # Initialize quantity if it doesn't exist
                                if 'quantity' not in locals() or not quantity:
                                    quantity = "N/A"
                                else:
                                    quantity = quantity.strip()
                                
                                # Only store if the data looks valid
                                if (len(name) > 0 and 
                                    'not found' not in name.lower() and 
                                    'carrot' in name.lower() and
                                    price.replace('.', '').isdigit()):
                                    
                                    # Append to lists
                                    product_data['Name'].append(name)
                                    product_data['Price'].append(float(price))  # Convert price to float
                                    product_data['Quantity'].append(quantity)
                                    product_data['Origin'].append(origin_text)
                
                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error finding products: {e}")
            driver.save_screenshot("error_state.png")
        
        # Debug: Print current URL
        print(f"Current URL: {driver.current_url}")
        
        # Debug: Save page source before product search
        with open("debug_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved page source to debug_source.html")
        
        # Find all elements with 'product' in their class or id
        all_product_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'product') or contains(@id, 'product')]")
        print("\nFound elements containing 'product':")
        for elem in all_product_elements[:3]:  # Show first 3 matches
            print("\nElement:")
            print("Tag:", elem.tag_name)
            print("Class:", elem.get_attribute('class'))
            print("ID:", elem.get_attribute('id'))
        
        # Find all elements with specific attributes that might contain products
        print("\nChecking common product container patterns:")
        patterns = [
            "//div[contains(@class, 'grid')]",
            "//div[contains(@class, 'list')]",
            "//div[contains(@class, 'card')]",
            "//section[contains(@class, 'products')]",
            "//div[contains(@class, 'search-results')]"
        ]

        for pattern in patterns:
            elements = driver.find_elements(By.XPATH, pattern)
            if elements:
                print(f"\nFound {len(elements)} elements matching: {pattern}")
                # Show sample of first element
                print("Sample element classes:", elements[0].get_attribute('class'))
        
        # Set viewport size for consistency
        driver.set_window_size(1920, 1080)
        
        # Find products using the most specific selector
        selector = 'div[class*="productList"] > div'
        products = driver.find_elements(By.CSS_SELECTOR, selector)
        
        if products:
            # Process products in parallel
            valid_products = []
            with ThreadPoolExecutor(max_workers=3) as executor:
                process_func = partial(process_product, driver, driver.current_window_handle)
                futures = [executor.submit(process_func, product) for product in products]
                for future in futures:
                    result = future.result()
                    if result:
                        valid_products.append(result)

            # Update product_data with valid_products
            for product in valid_products:
                product_data['Name'].append(product['name'])
                product_data['Price'].append(product['price'])
                product_data['Quantity'].append(product['quantity'])
                product_data['Origin'].append(product['origin'])
        else:
            print("No products found")
            
        # Add detailed element inspection
        print("\nInspecting page structure:")

        # First, let's check all divs with grid classes
        grid_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid')]")
        for i, grid in enumerate(grid_elements):
            print(f"\nGrid {i+1}:")
            print("Classes:", grid.get_attribute('class'))
            print("Child elements:", len(grid.find_elements(By.XPATH, ".//*")))
            
            # Print first level children
            children = grid.find_elements(By.XPATH, "./*")
            print("\nDirect children:")
            for child in children[:3]:  # First 3 children
                print("\nChild element:")
                print("Tag:", child.tag_name)
                print("Class:", child.get_attribute('class'))
                print("Text content:", child.text[:100] if child.text else "No text")

        # Let's also check for any elements containing 'card' or 'item'
        print("\nSearching for card/item elements:")
        card_items = driver.find_elements(By.XPATH, "//*[contains(@class, 'card') or contains(@class, 'item')]")
        for i, item in enumerate(card_items[:3]):
            print(f"\nItem {i+1}:")
            print("Tag:", item.tag_name)
            print("Class:", item.get_attribute('class'))
            print("Parent class:", item.find_element(By.XPATH, "..").get_attribute('class'))

        # Take a screenshot for visual reference
        driver.save_screenshot("page_state.png")
        
        # Add this before creating the DataFrame (after the product loop):
        try:
            df = pd.DataFrame(product_data)
            print("\nData to be saved:")
            print(df)
            
            # Sort by price for better readability
            df = df.sort_values('Price')
            
            # Add some data cleaning
            df['Price'] = df['Price'].astype(float)  # Ensure prices are floats
            df['Name'] = df['Name'].str.strip()  # Clean whitespace
            df['Quantity'] = df['Quantity'].str.strip()
            df['Origin'] = df['Origin'].str.strip()
            
            # Remove any rows where essential data is missing
            df = df.dropna(subset=['Name', 'Price'])
            
            # Save to Excel with some formatting
            with pd.ExcelWriter('carrot_prices.xlsx', engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Carrot Prices', index=False)
                
                # Get the workbook and the worksheet
                workbook = writer.book
                worksheet = writer.sheets['Carrot Prices']
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            print(f"\nSuccessfully saved {len(df)} products to carrot_prices.xlsx")
        except Exception as e:
            print(f"Error saving to Excel: {e}")
            print("Product data:", product_data)
        
    except Exception as e:
        print(f"Browser initialization error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

def process_product(driver, main_window, product):
    try:
        # Extract basic product info
        name = product.find_element(By.CSS_SELECTOR, 
            "div.text-sm.leading-4.font-medium.line-clamp-2 span").text.strip()
        quantity = product.find_element(By.CSS_SELECTOR, 
            "div.text-sm.leading-4.font-medium.truncate.text-gray-500").text.strip()
        price = product.find_element(By.CSS_SELECTOR, 
            "div.text-lg.leading-5.font-bold").text.strip()
        
        # Get product link and origin in a separate thread
        product_link = product.find_element(By.TAG_NAME, "a").get_attribute("href")
        
        # Open in new tab
        driver.execute_script(f'window.open("{product_link}","_blank");')
        driver.switch_to.window(driver.window_handles[-1])
        
        # Quick wait for origin element
        origin_text = "N/A"
        try:
            origin_elem = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'css-p1qrqm')]"))
            )
            origin_text = origin_elem.text.replace('Origin -', '').strip()
        except:
            pass
        
        # Close tab and switch back
        driver.close()
        driver.switch_to.window(main_window)
        
        return {
            'name': name,
            'price': float(price.replace('AED', '').strip()),
            'quantity': quantity,
            'origin': origin_text
        }
    except Exception as e:
        return None

if __name__ == '__main__':
    search_carrots()
