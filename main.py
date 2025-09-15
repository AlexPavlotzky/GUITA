import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk
from datetime import datetime, timedelta
import db
import uuid

class TransactionsView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.currency = "€"  # Divisa por defecto: € (euro)
        self.current_month = datetime.now().replace(day=1)
        self.selected_type = 1  # Por defecto: Gasto

        # --- Stack principal ---
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(200)

        # Tabla de transacciones
        self.store = Gtk.ListStore(str, str, str, int, str, str, str)
        self.view = Gtk.TreeView(model=self.store)
        self.view.set_vexpand(True)
        self.view.set_halign(Gtk.Align.CENTER)

        # GestureClick para detectar click derecho
        gesture = Gtk.GestureClick()
        gesture.set_button(3)  # botón derecho
        gesture.connect("pressed", self.on_right_click)
        self.view.add_controller(gesture)

        columns = ["Fecha", "Monto", "Tipo", "Categoría", "Descripción", "Cuenta"]
        for i, title in enumerate(columns):
            # Renderer para las celdas
            renderer = Gtk.CellRendererText()
            renderer.set_property("xalign", 0.5)  # centra el texto dentro de la celda
        
            # Crear columna y añadir renderer
            column = Gtk.TreeViewColumn()
            column.set_resizable(False)
            column.pack_start(renderer, True)
            column.add_attribute(renderer, "text", i+1)
        
            # Header: label centrado y en negrita
            header_label = Gtk.Label()
            header_label.set_markup(f"<b>{title}</b>")
            header_label.set_hexpand(True)
            header_label.set_halign(Gtk.Align.CENTER)
        
            column.set_widget(header_label)
            column.set_clickable(False)
        
            self.view.append_column(column)

        box_table = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Header mes
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.prev_button = Gtk.Button(label="<")
        self.prev_button.connect("clicked", self.on_prev_month)
        self.next_button = Gtk.Button(label=">")
        self.next_button.connect("clicked", self.on_next_month)
        self.month_label = Gtk.Label(label=self.current_month.strftime("%B %Y"))
        self.month_label.set_hexpand(True)
        self.month_label.set_halign(Gtk.Align.CENTER)
        header.append(self.prev_button)
        header.append(self.month_label)
        header.append(self.next_button)
        header.set_halign(Gtk.Align.CENTER)
        header.set_margin_top(50)
        box_table.append(header)

        # Separador entre header y resumen
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator1.set_margin_top(5)
        separator1.set_margin_bottom(5)
        box_table.append(separator1)

        # Resumen mensual
        summary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        self.label_saving = Gtk.Label(label="Ahorros: 0 €")
        self.label_income = Gtk.Label(label="Ganancia: 0 €")
        self.label_expense = Gtk.Label(label="Gasto: 0 €")
        self.label_balance = Gtk.Label(label="Saldo: 0 €")
        self.label_debt = Gtk.Label(label="Deuda: 0 €")
        summary_box.append(self.label_saving)
        summary_box.append(self.label_income)
        summary_box.append(self.label_expense)
        summary_box.append(self.label_balance)
        summary_box.append(self.label_debt)
        summary_box.set_halign(Gtk.Align.CENTER)
        box_table.append(summary_box)
        
        # Separador entre resumen y tabla
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_top(5)
        separator2.set_margin_bottom(5)
        box_table.append(separator2)

        # Scroll con tabla
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.view)
        scroll.set_vexpand(True)           # que intente expandirse
        scroll.set_min_content_height(200) # altura mínima de la tabla
        scroll.set_max_content_height(400) # altura máxima de la tabla
        box_table.append(scroll)
         
        # Botón + en la parte inferior
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_button = Gtk.Button(label="+")
        self.add_button.connect("clicked", lambda b: self.stack.set_visible_child_name("form"))
        bottom_box.append(self.add_button)
        bottom_box.set_halign(Gtk.Align.CENTER)
        bottom_box.set_margin_bottom(10)
        box_table.append(bottom_box)
        
        # Agregar al stack
        self.stack.add_named(box_table, "list")

        # --- Formulario dinámico - Agregar Transacción ---
        self.form_stack = Gtk.Stack()
        self.form_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.form_stack.set_transition_duration(150)
        
        # Ganancia
        income_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        income_box.append(Gtk.Label(label="Fecha:"))
        self.income_entry_date = Gtk.Entry()
        self.income_entry_date.set_text(datetime.now().strftime("%Y-%m-%d"))
        income_box.append(self.income_entry_date)
        
        income_box.append(Gtk.Label(label="Importe:"))
        self.income_entry_amount = Gtk.Entry()
        income_box.append(self.income_entry_amount)
        
        income_box.append(Gtk.Label(label="Categoría:"))
        self.income_category = Gtk.ComboBoxText()
        for uid, name, tipo in db.get_categories(): 
            if tipo == 0: 
                self.income_category.append(str(uid), name) 
            self.income_category.set_active(0)
        income_box.append(self.income_category)
        
        income_box.append(Gtk.Label(label="Cuenta:"))
        self.income_account = Gtk.ComboBoxText()
        for uid, name in db.get_accounts():
            self.income_account.append(str(uid), name)
        self.income_account.set_active(0)
        income_box.append(self.income_account)
        
        income_box.append(Gtk.Label(label="Descripción:"))
        self.income_entry_desc = Gtk.Entry()
        income_box.append(self.income_entry_desc)
        
        self.form_stack.add_named(income_box, "income")

        # Gasto
        expense_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        expense_box.append(Gtk.Label(label="Fecha:"))
        self.expense_entry_date = Gtk.Entry()
        self.expense_entry_date.set_text(datetime.now().strftime("%Y-%m-%d"))
        expense_box.append(self.expense_entry_date)
                
        expense_box.append(Gtk.Label(label="Importe:"))
        self.expense_entry_amount = Gtk.Entry()
        expense_box.append(self.expense_entry_amount)
        
        expense_box.append(Gtk.Label(label="Categoría:"))
        self.expense_category = Gtk.ComboBoxText()
        for uid, name, tipo in db.get_categories(): 
            if tipo == 1: 
                self.expense_category.append(str(uid), name) 
            self.expense_category.set_active(0)
        expense_box.append(self.expense_category)

        expense_box.append(Gtk.Label(label="Cuenta:"))
        self.expense_account = Gtk.ComboBoxText()
        for uid, name in db.get_accounts():
            self.expense_account.append(str(uid), name)
        self.expense_account.set_active(0)
        expense_box.append(self.expense_account)
        
        expense_box.append(Gtk.Label(label="Descripción:"))
        self.expense_entry_desc = Gtk.Entry()
        expense_box.append(self.expense_entry_desc)
        
        self.form_stack.add_named(expense_box, "expense")

        # Transferencia
        transfer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        transfer_box.append(Gtk.Label(label="Fecha:"))
        self.transfer_entry_date = Gtk.Entry()
        self.transfer_entry_date.set_text(datetime.now().strftime("%Y-%m-%d"))
        transfer_box.append(self.transfer_entry_date)
                
        transfer_box.append(Gtk.Label(label="Importe:"))
        self.transfer_entry_amount = Gtk.Entry()
        transfer_box.append(self.transfer_entry_amount)
        
        transfer_box.append(Gtk.Label(label="De:"))
        self.transfer_from = Gtk.ComboBoxText()
        for uid, name in db.get_accounts():
            self.transfer_from.append(str(uid), name)
        self.transfer_from.set_active(0)
        transfer_box.append(self.transfer_from)
        
        transfer_box.append(Gtk.Label(label="A:"))
        self.transfer_to = Gtk.ComboBoxText()
        for uid, name in db.get_accounts():
            self.transfer_to.append(str(uid), name)
        self.transfer_to.set_active(0)
        transfer_box.append(self.transfer_to)
        
        transfer_box.append(Gtk.Label(label="Descripción:"))
        self.transfer_entry_desc = Gtk.Entry()
        transfer_box.append(self.transfer_entry_desc)
        
        self.form_stack.add_named(transfer_box, "transfer")

        # Botones tipo arriba
        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.btn_income = Gtk.Button(label="Ganancia")
        self.btn_income.connect("clicked", lambda b: self.form_stack.set_visible_child_name("income"))
        self.btn_expense = Gtk.Button(label="Gasto")
        self.btn_expense.connect("clicked", lambda b: self.form_stack.set_visible_child_name("expense"))
        self.btn_transfer = Gtk.Button(label="Transferencia")
        self.btn_transfer.connect("clicked", lambda b: self.form_stack.set_visible_child_name("transfer"))
        type_box.append(self.btn_income)
        type_box.append(self.btn_expense)
        type_box.append(self.btn_transfer)

        # Botones aceptar/cancelar
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        accept_btn = Gtk.Button(label="Aceptar")
        accept_btn.connect("clicked", self.on_accept)
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", self.on_cancel)
        button_box.append(accept_btn)
        button_box.append(cancel_btn)

        form_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        form_main.append(type_box)
        form_main.append(self.form_stack)
        form_main.append(button_box)

        self.stack.add_named(form_main, "form")
        self.append(self.stack)

        self.load_transactions()

    # --- Métodos navegación lista ---
    def on_prev_month(self, button):
        first = self.current_month
        self.current_month = (first - timedelta(days=1)).replace(day=1)
        self.month_label.set_text(self.current_month.strftime("%B %Y"))
        self.load_transactions()

    def on_next_month(self, button):
        first = self.current_month
        month = first.month + 1
        year = first.year
        if month > 12:
            month = 1
            year += 1
        self.current_month = first.replace(year=year, month=month, day=1)
        self.month_label.set_text(self.current_month.strftime("%B %Y"))
        self.load_transactions()

    def on_cancel(self, button):
        self.stack.set_visible_child_name("list")

    def on_accept(self, button):

        tipo_name = self.form_stack.get_visible_child_name()
        if tipo_name == "income":
            tipo = 0
            date_uid = self.income_entry_date.get_text()
            amount_uid =float(self.income_entry_amount.get_text())
            category_uid = self.income_category.get_active_id()
            account_uid = self.income_account.get_active_id()
            to_account_uid = None
            desc_uid = self.income_entry_desc.get_text ()
        elif tipo_name == "expense":
            tipo = 1
            date_uid = self.expense_entry_date.get_text()
            amount_uid =float(self.expense_entry_amount.get_text())
            category_uid = self.expense_category.get_active_id()
            account_uid = self.expense_account.get_active_id()
            to_account_uid = None
            desc_uid = self.expense_entry_desc.get_text ()
        elif tipo_name == "transfer":
            tipo = 3
            date_uid = self.transfer_entry_date.get_text()
            amount_uid =float(self.transfer_entry_amount.get_text())
            category_uid = None
            account_uid = self.transfer_from.get_active_id()
            to_account_uid = self.transfer_to.get_active_id()
            desc_uid = self.transfer_entry_desc.get_text ()

        db.insert_transaction(date_uid, amount_uid, desc_uid, tipo, category_uid, account_uid, to_account_uid)
        self.stack.set_visible_child_name("list")
        self.load_transactions()

    def load_transactions(self):
        self.store.clear()
        income_total = 0.0
        expense_total = 0.0
        saving_total = 0.0      # Ahorros
        debt_last_month = 0.0
        debt_total = 0.0
        all_tx = db.get_transactions(limit=None)

        for tx in all_tx:
            uid = tx[0]
            tx_date = datetime.strptime(tx[1], "%Y-%m-%d")
            amount = float(tx[2]) 
            formatted_amount = f"{amount:.2f} {self.currency}"
            tipo = tx[3]
            cuenta = tx[6]
            categoria_uid = tx[7]
            
            if tx_date.year == self.current_month.year and tx_date.month == self.current_month.month:

                # --- Mostrar transacciones del mes actual ---
                self.store.append((
                    uid, # uid 
                    tx[1], # fecha
                    formatted_amount, # monto 
                    tx[3], # tipo 
                    tx[4], # categoría 
                    tx[5], # descripción 
                    tx[6] # cuenta 
                    )) 

                # --- Calcular resumen del mes: Ganancia, Gasto y Deuda --- 

                if tipo == 0: # ingreso 
                    income_total += amount
                #Sumamos todas las deudas del mes 
                if tipo == 0 and categoria_uid == "06a99f52-f910-49ee-885b-45b513aecdb0": 
                    debt_total += amount
                if tipo == 1: # gasto 
                    expense_total += amount 
                if tipo == 4 and cuenta == "Debiti": 
                    expense_total += amount
                    debt_total -= amount

            if (tx_date.year < self.current_month.year) or ( 
                tx_date.year == self.current_month.year and tx_date.month < self.current_month.month): 

                # --- Calcular saldo del mes anterior (Ahorro) ---

                if tipo == 0: 
                    saving_total += amount
                if tipo == 0 and categoria_uid == "06a99f52-f910-49ee-885b-45b513aecdb0": 
                    debt_last_month += amount
                if tipo == 1:
                    saving_total -= amount 
                if tipo == 4 and cuenta == "Debiti": 
                    saving_total -= amount
                    debt_total -= amount

        balance_total = saving_total + income_total - expense_total
        debt_total = debt_total + debt_last_month

        # --- Actualizar labels --- 
        self.label_saving.set_text(f"Ahorros: {saving_total:.2f} {self.currency}") 
        self.label_income.set_text(f"Ganancia: {income_total:.2f} {self.currency}") 
        self.label_expense.set_text(f"Gasto: {expense_total:.2f} {self.currency}") 
        self.label_balance.set_text(f"Saldo: {balance_total:.2f} {self.currency}") 
        self.label_debt.set_text(f"Deudas: {debt_total:.2f} {self.currency}")
        
    def on_right_click(self, gesture, n_press, x, y):
        path_info = self.view.get_path_at_pos(int(x), int(y))
        if path_info is not None:
            path, col, cell_x, cell_y = path_info

            # Seleccionar la fila bajo el cursor
            self.view.grab_focus()
            self.view.set_cursor(path, col, 0)

            # Crear menú contextual 
            menu = Gtk.PopoverMenu() 
            menu_model = Gio.Menu()
            menu_model.append("Editar", "app.edit_transaction") 
            menu_model.append("Eliminar", "app.delete_transaction")    
            menu.set_menu_model(menu_model)
            menu.set_has_arrow(False)
            menu.set_pointing_to(Gdk.Rectangle(int(x), int(y), 1, 1))
            menu.set_parent(self.view)
            menu.popup()

class StatisticsView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        label = Gtk.Label(label="Estadísticas del mes (próximamente)")
        label.set_halign(Gtk.Align.CENTER)
        self.append(label)

class AccountsView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.currency = "€"
        self.store = Gtk.ListStore(str, str)
        view = Gtk.TreeView(model=self.store)
        view.set_vexpand(True)
        view.set_halign(Gtk.Align.CENTER)

        columns = ["Cuenta", "Saldo"]
        for i, title in enumerate(columns):
            renderer = Gtk.CellRendererText()
            renderer.set_property("xalign", 0.5)
            column = Gtk.TreeViewColumn()
            column.set_resizable(False)
            column.pack_start(renderer, True)
            column.add_attribute(renderer, "text", i)
            header_label = Gtk.Label()
            header_label.set_markup(f"<b>{title}</b>")
            header_label.set_hexpand(True)
            header_label.set_halign(Gtk.Align.CENTER)
        
            column.set_widget(header_label)
            column.set_clickable(False)
        
            view.append_column(column)

        
        box_table = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        separator1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator1.set_margin_top(5)
        separator1.set_margin_bottom(5)
        box_table.append(separator1)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(view)
        scroll.set_vexpand(True)           # que intente expandirse
        scroll.set_min_content_height(200) # altura mínima de la tabla
        scroll.set_max_content_height(400) # altura máxima de la tabla
        box_table.append(scroll)

        self.append(box_table)

        self.load_accounts()

    def load_accounts(self):
        self.store.clear()
        balances = db.get_account_balances()
        for name, balance in balances:
            try:
                amount = float(balance)
                formatted_amount = f"{amount:.2f} {self.currency}"
                self.store.append((
                   name, formatted_amount
                ))
            except:
                continue

class GuitaApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.guita.app")

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action1 = Gio.SimpleAction.new("delete_transaction", None)
        action1.connect("activate", self.on_delete_transaction)
        action2 = Gio.SimpleAction.new("edit_transaction", None)
        action2.connect("activate", self.on_edit_transaction)
        self.add_action(action1)
        self.add_action(action2)
        

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("GUITA")
        window.set_default_size(1000, 600)
    
        # --- Stack principal ---
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(200)
    
        # --- Vistas ---
        self.transactions_view = TransactionsView()
        self.accounts_view = AccountsView()
        self.statistics_view = StatisticsView()
    
        stack.add_named(self.transactions_view, "transactions")
        stack.add_named(self.accounts_view, "accounts")
        stack.add_named(self.statistics_view, "statistics")
            
        # --- Título global ---
        title_label = Gtk.Label(label="GUITA")
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.set_margin_top(10)
        title_label.set_markup("<b>GUITA</b>")

        # --- Subtítulo global ---
        subtitle_label = Gtk.Label(label="Graphical User Interface for Transactions & Accounts")
        subtitle_label.set_halign(Gtk.Align.CENTER)
        subtitle_label.set_margin_top(6)
        subtitle_label.set_margin_bottom(10)
    
        # --- Botones de navegación ---
        btn_transactions = Gtk.Button(label="Transacciones")
        btn_transactions.connect("clicked", lambda b: stack.set_visible_child_name("transactions"))
            
        btn_accounts = Gtk.Button(label="Cuentas")
        btn_accounts.connect("clicked", lambda b: stack.set_visible_child_name("accounts"))

        btn_statistics = Gtk.Button(label="Estadísticas")
        btn_statistics.connect("clicked", lambda b: stack.set_visible_child_name("statistics"))
    
        menu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        menu_box.append(btn_transactions)
        menu_box.append(btn_accounts)
        menu_box.append(btn_statistics)
        menu_box.set_halign(Gtk.Align.CENTER)
        menu_box.set_margin_top(20)
    
        # --- Layout principal ---
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.append(title_label)
        vbox.append(subtitle_label)
        vbox.append(menu_box)
        vbox.append(stack)
    
        window.set_child(vbox)
        window.present()
        
    def on_delete_transaction(self, action, param):
        selection = self.transactions_view.view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            uid = model[treeiter][0]   # primera columna = uid
            date = model[treeiter][1]
            desc = model[treeiter][2]
    
            # Borrar en DB
            db.delete_transaction(uid) 

            # Refrescar la tabla    
            self.transactions_view.load_transactions()
            self.accounts_view.load_accounts()

    def on_edit_transaction(self, action, param):
        selection = self.transactions_view.view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            uid = model[treeiter][0]   # primera columna = uid
            date = model[treeiter][1]
            desc = model[treeiter][2]

if __name__ == "__main__":
    app = GuitaApp()
    app.run()
