class SettingsScreen:
    def __init__(self):
        self.expense_types = []
        self.income_types = []
        self.budget = 0

    def add_expense_type(self, expense_type):
        self.expense_types.append(expense_type)

    def add_income_type(self, income_type):
        self.income_types.append(income_type)

    def set_budget(self, budget):
        self.budget = budget

    def generate_report(self):
        # Logic to generate reports based on the data
        pass

    def display_settings(self):
        # Logic to display the settings interface
        pass