import streamlit as st
import json
import os

DATA_FILE = "inventory_data.json"
ORDER_FILE = "order_queue.json"

# ---------------- PRODUCT CLASS ----------------
class Product:
    def __init__(self, product_id, name, quantity, price):
        self.product_id = product_id
        self.name = name
        self.quantity = quantity
        self.price = price
        self.next = None

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "quantity": self.quantity,
            "price": self.price
        }

# ---------------- INVENTORY (LINKED LIST) ----------------
class Inventory:
    def __init__(self):
        self.head = None
        self.load_from_file()

    def add_product(self, product_id, name, quantity, price):
        if self.search_product(product_id) or self.search_product_by_name(name):
            raise ValueError("Product with this ID or name already exists.")
        new = Product(product_id, name, quantity, price)
        new.next = self.head
        self.head = new
        self.save_to_file()

    def delete_product(self, product_id):
        curr, prev = self.head, None
        while curr:
            if curr.product_id == product_id:
                if prev:
                    prev.next = curr.next
                else:
                    self.head = curr.next
                self.save_to_file()
                return
            prev, curr = curr, curr.next
        raise ValueError("Product not found")

    def update_quantity(self, product_id, change):
        prod = self.search_product(product_id)
        if not prod:
            raise ValueError("Product not found")
        if prod.quantity + change < 0:
            raise ValueError("Insufficient stock")
        prod.quantity += change
        self.save_to_file()

    def search_product(self, product_id):
        curr = self.head
        while curr:
            if curr.product_id == product_id:
                return curr
            curr = curr.next
        return None

    def search_product_by_name(self, name):
        curr = self.head
        while curr:
            if curr.name.lower() == name.lower():
                return curr
            curr = curr.next
        return None

    def display_inventory(self):
        items = []
        curr = self.head
        while curr:
            items.append(curr)
            curr = curr.next
        return items

    def to_list(self):
        lst = []
        curr = self.head
        while curr:
            lst.append(curr)
            curr = curr.next
        return lst

    def from_list(self, lst):
        self.head = None
        for p in reversed(lst):
            p.next = self.head
            self.head = p
        self.save_to_file()

    # -------- MERGE SORT --------
    def merge_sort(self, key='id'):
        key_map = {'id': 'product_id', 'quantity': 'quantity', 'price': 'price'}

        def merge(left, right):
            result = []
            i = j = 0
            while i < len(left) and j < len(right):
                if getattr(left[i], key_map[key]) <= getattr(right[j], key_map[key]):
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1
            result.extend(left[i:])
            result.extend(right[j:])
            return result

        def sort_list(lst):
            if len(lst) <= 1:
                return lst
            mid = len(lst) // 2
            return merge(sort_list(lst[:mid]), sort_list(lst[mid:]))

        sorted_products = sort_list(self.to_list())
        self.from_list(sorted_products)

    def save_to_file(self):
        with open(DATA_FILE, 'w') as f:
            json.dump([p.to_dict() for p in self.to_list()], f, indent=4)

    def load_from_file(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.head = None
                    for item in reversed(data):
                        p = Product(item['product_id'], item['name'], item['quantity'], item['price'])
                        p.next = self.head
                        self.head = p
            except Exception:
                pass

# ---------------- ORDER QUEUE ----------------
class Order:
    def __init__(self, product_id, quantity):
        self.product_id = product_id
        self.quantity = quantity

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "quantity": self.quantity
        }

class OrderQueue:
    def __init__(self):
        self.queue = []
        self.load_from_file()

    def enqueue(self, order):
        self.queue.append(order)
        self.save_to_file()

    def dequeue(self):
        if self.queue:
            order = self.queue.pop(0)
            self.save_to_file()
            return order
        return None

    def save_to_file(self):
        with open(ORDER_FILE, 'w') as f:
            json.dump([o.to_dict() for o in self.queue], f, indent=4)

    def load_from_file(self):
        if os.path.exists(ORDER_FILE):
            try:
                with open(ORDER_FILE, 'r') as f:
                    data = json.load(f)
                    self.queue = [Order(d['product_id'], d['quantity']) for d in data]
            except Exception:
                self.queue = []

# ---------------- STREAMLIT UI ----------------
inventory = Inventory()
orders = OrderQueue()

st.set_page_config(page_title="Inventory Manager", layout="wide")
st.title("📦 Inventory Management System")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["➕ Add Product", "📋 Inventory", "🛒 Orders", "🔍 Sort/Search", "📄 Display"]
)

# -------- TAB 1 --------
with tab1:
    st.header("Add New Product")
    with st.form("add_product"):
        pid = st.text_input("Product ID")
        name = st.text_input("Product Name")
        qty = st.number_input("Quantity", min_value=0, step=1)
        price = st.number_input("Price", min_value=0.0, step=0.01)
        if st.form_submit_button("Add"):
            try:
                inventory.add_product(pid, name, qty, price)
                st.success("Product added successfully!")
            except ValueError as e:
                st.error(e)

# -------- TAB 2 --------
with tab2:
    st.header("Inventory")
    for prod in inventory.display_inventory():
        with st.expander(f"{prod.name} (ID: {prod.product_id})"):
            st.write(f"Quantity: {prod.quantity}")
            st.write(f"Price: ₹{prod.price:.2f}")

            col1, col2 = st.columns(2)
            with col1:
                add_qty = st.number_input("Add Quantity", min_value=0, step=1, key=f"a{prod.product_id}")
                if st.button("Update", key=f"u{prod.product_id}"):
                    inventory.update_quantity(prod.product_id, add_qty)
                    st.success("Updated")

            with col2:
                if st.button("Delete", key=f"d{prod.product_id}"):
                    inventory.delete_product(prod.product_id)
                    st.warning("Deleted")

# -------- TAB 3 --------
with tab3:
    st.header("Order Queue")
    with st.form("order_form"):
        pid = st.text_input("Product ID")
        qty = st.number_input("Order Quantity", min_value=1, step=1)
        if st.form_submit_button("Place Order"):
            prod = inventory.search_product(pid)
            if prod and prod.quantity >= qty:
                inventory.update_quantity(pid, -qty)
                st.success("Order fulfilled")
            else:
                orders.enqueue(Order(pid, qty))
                st.warning("Added to queue")

    st.subheader("Pending Orders")
    for o in orders.queue:
        st.write(f"ID: {o.product_id}, Qty: {o.quantity}")

# -------- TAB 4 --------
with tab4:
    st.header("Sort & Search")
    key = st.selectbox("Sort By", ["id", "quantity", "price"])
    if st.button("Sort"):
        inventory.merge_sort(key)
        st.success("Sorted")

    name = st.text_input("Search by Name")
    if name:
        p = inventory.search_product_by_name(name)
        if p:
            st.success(f"{p.name} | Qty: {p.quantity} | Price: ₹{p.price}")
        else:
            st.error("Not Found")

# -------- TAB 5 --------
with tab5:
    st.header("Inventory List")
    for p in inventory.display_inventory():
        st.write(f"{p.product_id} | {p.name} | {p.quantity} | ₹{p.price}")
