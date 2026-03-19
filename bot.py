# Importing Libraries
import playwright.async_api
from playwright.async_api import async_playwright, TimeoutError
import requests
import bs4
from bs4 import BeautifulSoup
import json
import re
from typing import Any
from nicegui import ui


# Creating the Bot Class
class Bot:

    BASE_URL: str = "https://us.supreme.com/collections/new"
    BASE_HEADERS: dict[str, str] = {"User-Agent": "Mozilla/5.0"}

    # Constructor
    def __init__(self, nations_codes: dict, zones_codes: dict) -> None:
        """
        Automation controller responsible for purchasing items on Supreme.

        This class:
        - Reads selected items from `items.json`
        - Scrapes Supreme product availability
        - Adds matching items to the cart
        - Completes the checkout flow using Playwright

        It acts as the execution layer for the UI-driven basket and checkout logic.

        Args:
            nations_codes (dict): Mapping of country names to country codes.
            zones_codes (dict): Mapping of country zones for shipping selection.
        """

        self.items: list[dict[str, Any]] = []
        self.selected_products: list[dict[str, Any]] = []
        self.update()

        # Storing Personal Data
        self.EMAIL = self.COUNTRY = self.FIRST_NAME = self.LAST_NAME = self.ADDRESS = ""
        self.POSTAL_CODE = self.CITY = self.PHONE = self.CARD_NUMBER = ""
        self.MONTH_EXP = self.YEAR_EXP = self.CVV = self.NAME_ON_CARD = self.ZONE = ""

        # Creating the Link's List
        self.links_list: list[str] = list()

        # Saving the list of nations and zones codes to convert
        self.nations_codes: dict = nations_codes
        self.zones_codes: dict = zones_codes

    def update(self) -> None:
        """
        Reload items from `items.json`.

        This method ensures the bot reflects any changes made
        to the basket before starting the automation process.
        """

        with open("items.json", "r") as i:
            raw_items: list[dict[str, Any]] = json.load(i)

        self.items = []
        for item in raw_items:
            normalized_item = dict(item)
            normalized_item["category"] = str(item.get("category", "")).replace("/", "-")
            normalized_item["color"] = str(item.get("color", "None")).strip()
            normalized_item["color_keywords"] = self._normalize_color_keywords(
                item.get("color_keywords", [])
            )
            normalized_item["allow_any_color"] = bool(item.get("allow_any_color", False))
            self.items.append(normalized_item)

    def _normalize_color_keywords(self, raw_keywords: Any) -> list[str]:
        """
        Normalize stored color keyword input into a list of regex-friendly strings.
        """
        if not raw_keywords:
            return []

        if isinstance(raw_keywords, str):
            return [
                keyword.strip()
                for keyword in raw_keywords.split(",")
                if keyword.strip()
            ]

        if isinstance(raw_keywords, list):
            return [
                str(keyword).strip()
                for keyword in raw_keywords
                if str(keyword).strip()
            ]

        return [str(raw_keywords).strip()]

    def _normalize_text(self, value: str | None) -> str:
        """
        Normalize text for stable title/color comparisons.
        """
        return re.sub(r"\s+", " ", value or "").strip().casefold()

    def _fetch_collection_data(self) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch and normalize Supreme's live collection JSON.
        """
        response: requests.models.Response = requests.get(
            self.BASE_URL, headers=self.BASE_HEADERS, timeout=10
        )
        response.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
        script_tag: bs4.element.Tag = soup.find("script", id="products-json")

        if not script_tag or not script_tag.text.strip():
            raise ValueError("No product JSON found on the page.")

        raw_data: dict[str, Any] = json.loads(script_tag.text.strip())
        structured: dict[str, list[dict[str, Any]]] = dict()

        for product in raw_data.get("products", []):
            category: str = product.get("product_type", "uncategorized").replace("/", "-")
            structured.setdefault(category, []).append(
                {
                    "title": product.get("title"),
                    "color": product.get("color"),
                    "url": product.get("url"),
                    "available": product.get("available"),
                }
            )

        return structured

    def _color_matches(self, live_color: str | None, item: dict[str, Any]) -> bool:
        """
        Match a live Supreme color against the stored basket preference.
        """
        normalized_live_color: str = self._normalize_text(live_color)
        exact_color: str = item.get("color", "None")
        color_keywords: list[str] = item.get("color_keywords", [])

        if exact_color not in {"", "None"} and normalized_live_color == self._normalize_text(exact_color):
            return True

        for keyword in color_keywords:
            try:
                if re.search(keyword, live_color or "", re.IGNORECASE):
                    return True
            except re.error:
                if self._normalize_text(keyword) in normalized_live_color:
                    return True

        if item.get("allow_any_color"):
            return True

        return False

    def _build_selection_plan(
        self, structured_data: dict[str, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """
        Build a match plan for all basket items using live Supreme product data.
        """
        plan: list[dict[str, Any]] = []

        for item in self.items:
            category_products: list[dict[str, Any]] = structured_data.get(
                item["category"], []
            )
            title_matches: list[dict[str, Any]] = [
                product
                for product in category_products
                if product.get("available")
                and self._normalize_text(product.get("title"))
                == self._normalize_text(item.get("name"))
            ]
            exact_matches: list[dict[str, Any]] = []
            keyword_matches: list[dict[str, Any]] = []

            for product in title_matches:
                if item.get("color", "None") not in {"", "None"} and (
                    self._normalize_text(product.get("color"))
                    == self._normalize_text(item.get("color"))
                ):
                    exact_matches.append(product)
                    continue

                if item.get("color_keywords") and self._color_matches(
                    product.get("color"), item
                ):
                    keyword_matches.append(product)

            selected_product: dict[str, Any] | None = None
            match_reason: str = "no live match"

            if exact_matches:
                selected_product = exact_matches[0]
                match_reason = "exact color match"
            elif keyword_matches:
                selected_product = keyword_matches[0]
                match_reason = "keyword/regex color match"
            elif item.get("allow_any_color") and title_matches:
                selected_product = title_matches[0]
                match_reason = "allow_any_color fallback"

            plan.append(
                {
                    "item": item,
                    "title_matches": title_matches,
                    "candidate_colors": sorted(
                        {
                            str(product.get("color", "Unknown")).strip()
                            for product in title_matches
                        }
                    ),
                    "selected_product": selected_product,
                    "match_reason": match_reason,
                }
            )

        return plan

    def _print_selection_plan(self, plan: list[dict[str, Any]], *, header: str) -> None:
        """
        Print a dry-run style summary of discovered live Supreme candidates.
        """
        print(f"\n=== {header} ===")
        for entry in plan:
            item: dict[str, Any] = entry["item"]
            selected_product: dict[str, Any] | None = entry["selected_product"]
            preferred_color = item.get("color", "None")
            color_keywords = item.get("color_keywords", [])
            print(
                f"- {item.get('name')} [{item.get('category')}]"
            )
            print(f"  preferred exact color: {preferred_color}")
            print(f"  preferred color keywords: {color_keywords or '[]'}")
            print(
                "  candidate colors: "
                f"{entry['candidate_colors'] or '[]'}"
            )
            for candidate in entry["title_matches"]:
                print(
                    "    "
                    f"{candidate.get('color')} -> https://us.supreme.com{candidate.get('url')}"
                )

            if selected_product:
                print(
                    "  selected: "
                    f"{selected_product.get('color')} "
                    f"({entry['match_reason']}) -> https://us.supreme.com{selected_product.get('url')}"
                )
            else:
                print(f"  selected: none ({entry['match_reason']})")

    async def dry_run(self) -> None:
        """
        Print live candidate colors and chosen URL for each basket item.
        """
        try:
            self.update()
            structured_data = self._fetch_collection_data()
            plan = self._build_selection_plan(structured_data)
            self._print_selection_plan(plan, header="SUPREMEBOT DRY RUN")
            matched_count: int = sum(1 for entry in plan if entry["selected_product"])
            ui.notify(
                f"Dry run complete. Matched {matched_count}/{len(plan)} item(s). See terminal for colors and URLs."
            )
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            ui.notify(f"Dry run failed: {e}")
            print(f"Dry run failed: {e}")

    # Scrape Method for Saving the URLs
    async def scrape(self) -> None:
        """
        Scrape Supreme's 'new' collection to locate product URLs.

        This method:
        - Fetches product JSON from Supreme
        - Matches products by name, color, and category
        - Stores valid product URLs for checkout
        """

        # Clear the live match state
        self.links_list.clear()
        self.selected_products.clear()

        try:
            structured_data: dict[str, list[dict[str, Any]]] = self._fetch_collection_data()
            plan: list[dict[str, Any]] = self._build_selection_plan(structured_data)
            self._print_selection_plan(plan, header="SUPREMEBOT LIVE MATCH")

            unmatched_items: list[str] = []
            for entry in plan:
                selected_product: dict[str, Any] | None = entry["selected_product"]
                if selected_product:
                    self.selected_products.append(entry)
                    self.links_list.append(
                        f"https://us.supreme.com{selected_product.get('url')}"
                    )
                else:
                    unmatched_items.append(entry["item"].get("name", "Unknown item"))

            if unmatched_items:
                ui.notify(
                    "No live color match for: "
                    + ", ".join(unmatched_items)
                )

        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            ui.notify(f"Error occurred: {e}")
            print(f"Error occurred: {e}")

    # Method for Add to Basket
    async def add_to_basket(self, page: playwright.async_api._generated.Page) -> None:
        """
        Add selected items to the Supreme cart.

        Args:
            page (Page): Active Playwright page instance.
        """
        for entry in self.selected_products:
            selected_product: dict[str, Any] = entry["selected_product"]
            item: dict[str, Any] = entry["item"]

            await page.goto(f"https://us.supreme.com{selected_product.get('url')}")

            selected_size: str = str(item.get("size", "None"))
            if selected_size not in {"", "None"}:
                try:
                    await page.wait_for_selector('select[aria-label="size"]', timeout=3000)
                    options: playwright.async_api._generated.ElementHandle = page.locator(
                        'select[aria-label="size"]'
                    )
                    if options:
                        await options.select_option(selected_size)
                except TimeoutError:
                    print(f"Size selector not found for {item.get('name')}, continuing.")

            add_button = page.locator(
                "input[data-type='product-add'], button[data-testid='add-to-cart-button']"
            ).first
            await add_button.click()
            await page.wait_for_timeout(1000)

    async def _go_to_checkout(self, page: playwright.async_api._generated.Page) -> None:
        """
        Try to navigate from the cart to checkout before falling back to the checkout URL.
        """
        await page.goto("https://us.supreme.com/cart")
        await page.wait_for_timeout(1000)

        for selector in [
            "a[href*='/checkout']",
            "button:has-text('Checkout')",
            "button:has-text('Check out')",
        ]:
            locator = page.locator(selector)
            if await locator.count():
                try:
                    await locator.first.click()
                    return
                except Exception:
                    continue

        await page.goto("https://us.supreme.com/checkout")

    async def _has_challenge(
        self, page: playwright.async_api._generated.Page
    ) -> bool:
        """
        Detect a likely captcha or checkout challenge without attempting bypass.
        """
        challenge_selectors = [
            "iframe[src*='captcha']",
            "iframe[src*='hcaptcha']",
            "iframe[src*='recaptcha']",
            "iframe[title*='challenge']",
            "[id*='captcha']",
            "[class*='captcha']",
            "[id*='challenge']",
            "[class*='challenge']",
        ]

        for selector in challenge_selectors:
            locator = page.locator(selector)
            try:
                if await locator.count() and await locator.first.is_visible():
                    return True
            except Exception:
                if await locator.count():
                    return True

        try:
            html = (await page.content()).lower()
        except Exception:
            return False

        return any(
            marker in html
            for marker in [
                "captcha",
                "verify you are human",
                "verify you're human",
                "security check",
                "challenge",
            ]
        )

    async def _wait_for_ready_or_manual_solve(
        self,
        page: playwright.async_api._generated.Page,
        ready_selectors: list[str],
        context: str,
        timeout_ms: int = 180000,
    ) -> None:
        """
        Wait for the next checkout stage to become ready, pausing for manual challenge solving if needed.
        """
        challenge_notified = False
        elapsed = 0

        while elapsed < timeout_ms:
            for selector in ready_selectors:
                locator = page.locator(selector)
                if await locator.count():
                    try:
                        if await locator.first.is_visible():
                            if challenge_notified:
                                ui.notify(f"{context} is ready again. Continuing Supremebot.")
                                print(f"{context} is ready again. Continuing Supremebot.")
                            return
                    except Exception:
                        return

            if await self._has_challenge(page) and not challenge_notified:
                message = (
                    f"Checkout challenge detected during {context}. "
                    "Solve it manually in the browser; Supremebot will resume automatically."
                )
                ui.notify(message)
                print(message)
                challenge_notified = True

            await page.wait_for_timeout(1000)
            elapsed += 1000

        raise TimeoutError(f"{context} did not become ready before timeout.")

    async def _fill_locator_value(
        self,
        locator: playwright.async_api._generated.Locator,
        value: str,
    ) -> bool:
        """
        Fill a locator, falling back to typed input for masked payment fields.
        """
        try:
            await locator.click()
        except Exception:
            pass

        try:
            await locator.fill(value)
            return True
        except Exception:
            pass

        try:
            await locator.type(value, delay=40)
            return True
        except Exception:
            return False

    async def _fill_payment_field(
        self,
        page: playwright.async_api._generated.Page,
        *,
        field_name: str,
        value: str,
        frame_selectors: list[str],
        input_selectors: list[str],
        frame_hints: list[str],
    ) -> None:
        """
        Fill a hosted checkout payment field across several iframe/input layouts.
        """
        if not value:
            return

        # Try direct inputs first in case the checkout renders them without iframes.
        for input_selector in input_selectors:
            locator = page.locator(input_selector).first
            try:
                if await locator.count() and await locator.is_visible():
                    if await self._fill_locator_value(locator, value):
                        return
            except Exception:
                continue

        # Then try iframe selectors against the page DOM.
        for frame_selector in frame_selectors:
            for input_selector in input_selectors:
                try:
                    locator = page.frame_locator(frame_selector).locator(
                        input_selector
                    ).first
                    if await locator.count():
                        if await self._fill_locator_value(locator, value):
                            return
                except Exception:
                    continue

        # Finally, scan loaded frames by URL/name hints.
        for frame in page.frames:
            frame_key = f"{frame.url} {frame.name or ''}".lower()
            if not any(hint in frame_key for hint in frame_hints):
                continue

            for input_selector in input_selectors:
                try:
                    locator = frame.locator(input_selector).first
                    if await locator.count():
                        if await self._fill_locator_value(locator, value):
                            return
                except Exception:
                    continue

        raise TimeoutError(f"Unable to find payment field: {field_name}")

    # Method for Checkout
    async def checkout(self, page: playwright.async_api._generated.Page) -> None:
        """
        Complete the checkout form on Supreme.

        Args:
            page (Page): Active Playwright page instance.
        """

        await self._go_to_checkout(page)
        await self._wait_for_ready_or_manual_solve(
            page,
            ["input[id='email']", "select[name='countryCode']"],
            "checkout form",
        )

        terms_checkbox = page.locator('input[type="checkbox"]').first
        if await terms_checkbox.count():
            try:
                await terms_checkbox.check()
            except Exception:
                await terms_checkbox.click()

        # Filling the Checkout Form
        await page.fill('input[id="email"]', self.EMAIL)
        await page.locator('select[name="countryCode"]').select_option(
            self.nations_codes[self.COUNTRY]
        )
        await page.fill('input[name="firstName"]', self.FIRST_NAME)
        await page.fill('input[name="lastName"]', self.LAST_NAME)
        await page.fill('input[name="address1"]', self.ADDRESS)
        await page.fill('input[name="postalCode"]', self.POSTAL_CODE)
        await page.fill('input[name="city"]', self.CITY)

        try:
            await page.wait_for_selector('select[name="zone"]')
            zone_select = page.locator('select[name="zone"]')
            await zone_select.select_option(self.zones_codes[self.COUNTRY][self.ZONE])
            await page.wait_for_timeout(1500)
        except Exception:
            pass

        await page.fill('input[name="phone"]', self.PHONE)

        await self._wait_for_ready_or_manual_solve(
            page,
            [
                "iframe[src*='checkout.shopifycs.com/number']",
                "iframe[title*='Card number']",
                "iframe[name*='number']",
                "iframe[id*='number']",
                "input[name='number']",
                "input[autocomplete='cc-number']",
            ],
            "payment fields",
        )

        await self._fill_payment_field(
            page,
            field_name="card number",
            value=self.CARD_NUMBER,
            frame_selectors=[
                'iframe[src*="checkout.shopifycs.com/number"]',
                'iframe[title*="Card number"]',
                'iframe[name*="number"]',
                'iframe[id*="number"]',
            ],
            input_selectors=[
                'input[name="number"]',
                'input[autocomplete="cc-number"]',
                'input[placeholder*="Card number"]',
                'input[inputmode="numeric"]',
            ],
            frame_hints=["number", "card", "payment"],
        )

        await self._fill_payment_field(
            page,
            field_name="expiry",
            value=f"{self.MONTH_EXP}/{self.YEAR_EXP}",
            frame_selectors=[
                'iframe[src*="checkout.shopifycs.com/expiry"]',
                'iframe[title*="Expiration"]',
                'iframe[title*="Expiry"]',
                'iframe[name*="expiry"]',
                'iframe[id*="expiry"]',
            ],
            input_selectors=[
                'input[name="expiry"]',
                'input[autocomplete="cc-exp"]',
                'input[placeholder*="MM / YY"]',
                'input[placeholder*="Expiration"]',
            ],
            frame_hints=["expiry", "exp", "payment"],
        )

        await self._fill_payment_field(
            page,
            field_name="security code",
            value=self.CVV,
            frame_selectors=[
                'iframe[src*="checkout.shopifycs.com/verification_value"]',
                'iframe[title*="Security code"]',
                'iframe[title*="CVV"]',
                'iframe[name*="verification"]',
                'iframe[id*="verification"]',
                'iframe[name*="cvv"]',
                'iframe[id*="cvv"]',
            ],
            input_selectors=[
                'input[name="verification_value"]',
                'input[autocomplete="cc-csc"]',
                'input[placeholder*="Security code"]',
                'input[placeholder*="CVV"]',
            ],
            frame_hints=["verification", "security", "cvv", "payment"],
        )

        await self._fill_payment_field(
            page,
            field_name="name on card",
            value=self.NAME_ON_CARD,
            frame_selectors=[
                'iframe[src*="checkout.shopifycs.com/name"]',
                'iframe[title*="Name on card"]',
                'iframe[name*="name"]',
                'iframe[id*="name"]',
            ],
            input_selectors=[
                'input[name="name"]',
                'input[autocomplete="cc-name"]',
                'input[placeholder*="Name on card"]',
            ],
            frame_hints=["name", "cardholder", "payment"],
        )

    # Function to start the bot
    async def start(self) -> None:
        """
        Entry point to start the full automation process.

        This method:
        - Reloads basket data
        - Scrapes available products
        - Launches the browser
        - Adds items to the cart
        - Fills the checkout form
        """
        try:

            # Update the info if something is changed
            self.update()

            # Start the automation process
            await self.scrape()
            if not self.selected_products:
                ui.notify(
                    "No live Supreme matches found. Run the dry run and adjust your color keywords before starting."
                )
                return

            # Set up Playwright
            async with async_playwright() as p:
                browser: playwright.async_api._generated.Browser = (
                    await p.chromium.launch(headless=False)
                )
                page: playwright.async_api._generated.Page = await browser.new_page()

                # Add items to the basket
                await self.add_to_basket(page)

                try:
                    # Attempt to complete the checkout process
                    await self.checkout(page)

                    # Waiting for the user to submit the order
                    await page.pause()

                except TimeoutError as e:
                    ui.notify(f"Error: {e}")
                    print(e)
        except Exception as e:
            pass
