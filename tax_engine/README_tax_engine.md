# Uganda Tax Engine

**Course:** MSCS & MSDS OOP with Python, Assignment 2, Advent 2026
**Mini-project 2:** An extensible, testable tax calculator that models Uganda Revenue Authority (URA) tax rules using object-oriented Python.

**Author:** [Your full name] | **Student number:** [Your student number]
**Repository:** [Your GitHub repository link]

---

## 1. What this project does

The engine calculates the following taxes, each as its own class:

| Module | What it calculates |
|---|---|
| **PAYE** | Monthly Pay As You Earn on gross pay plus allowances, using progressive bands and a 10% surcharge above UGX 10,000,000 |
| **NSSF** | Employee contribution (5% of gross) and employer contribution (10% of gross) |
| **Local Service Tax** | A configurable flat monthly amount, deducted before PAYE |
| **Payroll pipeline** | Runs NSSF, Local Service Tax and PAYE in a documented order and produces a payslip with net pay |
| **VAT** | Output VAT, input VAT and net VAT payable from standard-rated, zero-rated and exempt supplies |
| **Corporate income tax** | 30% of chargeable income (revenue minus allowable deductions) for resident companies |
| **Tax planner (extension B)** | Compares two ways of receiving the same money (salary versus dividend) and reports the difference |

All money is handled with `decimal.Decimal` through a custom `Money` class. Floats are never used for money.

---

## 2. Repository structure

```
uganda-tax-engine/
├── README.md
├── requirements.txt
├── pytest.ini
├── .gitignore
├── project2_tax_engine.ipynb      # the executable notebook (imports from src/)
├── src/
│   └── tax_engine/
│       ├── __init__.py            # exports the public classes and calculators
│       ├── errors.py              # TaxError, InvalidIncomeError, NoScheduleForDateError
│       ├── money.py               # Money value object (UGX, Decimal only)
│       ├── models.py              # TaxContext, TaxResult
│       ├── base.py                # abstract Tax base class
│       ├── paye.py                # PAYE
│       ├── payroll.py             # NSSF, LocalServiceTax, Payslip, Payroll
│       ├── vat.py                 # VATCategory, Invoice, VATContext, VAT
│       ├── cit.py                 # Deduction, CITContext, CorporateIncomeTax
│       ├── planner.py             # Scenario, SalaryScenario, DividendScenario, TaxPlanner
│       └── calculators.py         # the interactive, text-based calculators
└── tests/
    ├── test_money.py
    ├── test_paye_boundaries.py
    ├── test_paye_properties.py    # hypothesis property-based tests
    ├── test_payroll.py
    ├── test_vat.py
    ├── test_cit.py
    ├── test_planner.py
    └── test_calculators.py        # calculators, with typed input simulated
```

Reusable logic lives in `src/`. The notebook imports it and demonstrates it.

---

## 3. Setup

**Requirements:** Python 3.10 or newer.

```bash
# 1. Clone the repository
git clone [your repository link]
cd uganda-tax-engine

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

`requirements.txt`:

```
notebook
pytest
hypothesis
```

`pytest.ini` (lets the tests find the `src/` folder):

```
[pytest]
pythonpath = src
```

---

## 4. How to run

### 4.1 The notebook

```bash
jupyter notebook project2_tax_engine.ipynb
```

Choose **Kernel → Restart & Run All**. The notebook runs top to bottom without errors and prints `PASS` for each inline test. The interactive calculators at the very end are **switched off by default** (`RUN_INTERACTIVE = False`) so that Run All never stops to wait for typing. See 4.3 to use them.

### 4.2 The tests

```bash
pytest -v
```

### 4.3 The interactive calculators

The four calculators live in `src/tax_engine/calculators.py` and are called from the last section of the notebook. To use them, change `RUN_INTERACTIVE = False` to `RUN_INTERACTIVE = True` in section 10 of the notebook, then run the calculator cells one at a time and type into the box that appears under each.

**Payroll calculator** (`payroll_calculator()`)
Asks for: monthly gross pay, allowances (Enter for 0), Local Service Tax for the month (Enter for 0), and whether the employee is a resident (y/n).
Prints: gross, NSSF, Local Service Tax, PAYE and net pay. Type `q` at the first question to quit.

**VAT calculator** (`vat_calculator()`)
Shows a numbered menu:

```
1 = Standard-rated sale (18% VAT)
2 = Zero-rated sale (e.g. exports)
3 = Exempt sale
4 = Purchase with VAT (standard-rated)
5 = Finish and show my VAT
```

Choose a number, then enter the amount **before VAT**. Repeat as many times as you need (amounts of the same type add up). Choose `5` to see output VAT, input VAT and net VAT payable. A negative net means a refund or credit.

**Corporate income tax calculator** (`cit_calculator()`)
Asks for total revenue and total allowable deductions (Enter for 0). Prints chargeable income and tax at 30%. A loss gives zero tax.

**Salary versus dividend planner** (`planner_calculator()`)
Asks for an amount and whether the person is a resident. Prints a side-by-side table of gross, deductions and net for each option and says which leaves more money.

Amounts can be typed with commas, for example `1,500,000`.

---

## 5. Using the code directly

```python
from decimal import Decimal
from tax_engine.models import TaxContext
from tax_engine.paye import PAYE
from tax_engine.payroll import Payroll

# PAYE on its own
ctx = TaxContext(gross_pay=Decimal("1000000"))
result = PAYE().calculate(ctx)
print(result.amount)            # UGX 188,250.00

# Full payslip
slip = Payroll(lst_monthly="0").run(ctx)
print(slip.nssf, slip.paye, slip.net)
```

```python
from tax_engine.money import Money
from tax_engine.vat import VAT, VATContext, Invoice, VATCategory

invoices = (
    Invoice("Local sale",  Money("1000000"), VATCategory.STANDARD, "sale"),
    Invoice("Export",      Money("500000"),  VATCategory.ZERO,     "sale"),
    Invoice("Packaging",   Money("400000"),  VATCategory.STANDARD, "purchase"),
)
summary = VAT().summary(VATContext(invoices))
print(summary.output_vat, summary.input_vat, summary.net_payable)
```

```python
from tax_engine.planner import TaxPlanner, SalaryScenario, DividendScenario

comparison = TaxPlanner().compare(SalaryScenario("1000000"), DividendScenario("1000000"))
print(comparison.better, comparison.net_difference)
```

---

## 6. Design

### 6.1 Classes and how they fit together

- **`Tax` (abstract base class)** defines `calculate(self, ctx: TaxContext) -> TaxResult`. `PAYE`, `NSSF`, `LocalServiceTax`, `VAT` and `CorporateIncomeTax` all implement it, so any tax can be used through the same interface.
- **`TaxContext` and `TaxResult`** are immutable dataclasses (`frozen=True`). The context carries the inputs (gross pay, allowances, residency, date) and the result carries the answer. `TaxContext.total_pay` is a property that adds allowances to gross pay.
- **`Money`** is a value object for Ugandan shillings. It implements `__add__`, `__sub__`, `__mul__`, `__rmul__`, `__lt__`, `__eq__`, `__hash__`, `__repr__` and `__str__`.
- **`Payroll`** is built by composition: it holds an `NSSF`, a `LocalServiceTax` and a `PAYE` and runs them in order.
- **`Scenario` (abstract)** with `SalaryScenario` and `DividendScenario`, compared by `TaxPlanner`.

### 6.2 Money handling

- `Money` accepts only `Decimal`, `int` or `str`. A `float` raises `TypeError`.
- Values are rounded **once**, in the constructor, to 2 decimal places using `ROUND_HALF_UP`. The rounding rule is chosen explicitly because Python's default for `Decimal` is `ROUND_HALF_EVEN`.
- Every operation returns a **new** `Money`, so no step can silently change another step's input.

### 6.3 Order of deductions in the payroll pipeline

1. **NSSF** is calculated on gross pay (gross plus allowances).
2. **Local Service Tax** is deducted next, **before** PAYE, because the assignment baseline lists it as an optional deduction applied before PAYE.
3. **PAYE** is calculated on pay after Local Service Tax.
4. **Net pay** = gross − NSSF − Local Service Tax − PAYE.

*Justification:* this follows the assignment baseline literally. NSSF is not subtracted before PAYE here. [Check the URA / NSSF documentation and state here whether NSSF should reduce taxable income, and cite it.]

### 6.4 Errors

A custom hierarchy is used, and invalid input raises an error instead of returning a wrong number (one known exception is the non-resident PAYE limitation in section 10):

```
TaxError
├── InvalidIncomeError         # negative income, float input, bad invoice or deduction
└── NoScheduleForDateError     # no rate schedule exists for the requested date
```

Unsupported cases, such as a non-resident company for corporate income tax, raise `TaxError` instead of guessing a rate.

### 6.5 Inheritance: where it is used and where it is avoided

**Used (an "is a" relationship):**

- `PAYE`, `NSSF`, `LocalServiceTax`, `VAT` and `CorporateIncomeTax` each *are a* `Tax`, so they share one interface and new taxes can be added without changing existing code.
- `SalaryScenario` and `DividendScenario` each *are a* `Scenario`, so `TaxPlanner` can compare any two scenarios.

**Deliberately avoided:**

- `Money` does **not** subclass `Decimal`. It wraps a `Decimal` instead, which lets it reject floats and block meaningless operations such as `Money * Money`.
- There are no `ResidentPAYE` and `NonResidentPAYE` subclasses. Residency is a value in `TaxContext`, not a different kind of object.
- `Payroll` does not inherit from the taxes. A payroll *has* an NSSF, a PAYE and a Local Service Tax, so it uses them by composition.
- `NSSF` does not inherit from `PAYE`. They share an interface, not an implementation.

---

## 7. Regulatory baseline

The rates below come from the assignment's sample baseline. **They must be confirmed against URA documentation.**

| Tax | Rule implemented | Source and version |
|---|---|---|
| PAYE (resident, monthly) | Nil up to 335,000; 20% of the excess over 335,000 up to 410,000; 15,000 + 25% of the excess over 410,000 up to 485,000; 33,750 + 30% of the excess over 485,000; plus 10% on the excess over 10,000,000 | [add source, version and date] |
| NSSF | Employee 5% of gross; employer 10% of gross | [add source, version and date] |
| VAT | Standard rate 18%; zero-rated and exempt supplies carry no output VAT | [add source, version and date] |
| Corporate income tax | 30% for resident companies | [add source, version and date] |
| Local Service Tax | Configurable flat monthly amount, optional | [add source, version and date] |
| Dividend withholding (planner) | 15% flat (assumption) | [add source, version and date] |

---

## 8. Testing

**Boundary tests** check the exact edges of every PAYE band: 335,000; 335,001; 410,000; 485,000; 10,000,000; and 10,000,001 (plus 410,001 and 485,001). They also check that negative income raises `InvalidIncomeError`.

**Property-based tests** use `hypothesis` to generate random incomes and check that PAYE:

- is never negative,
- never exceeds income,
- is monotonic (more income never means less tax).

**Other tests** check payroll, VAT, corporate income tax, `Money` (including rejection of floats), the planner and the interactive calculators (with typed input simulated) against figures worked out by hand.

**Expected failures:** two tests, `test_non_resident_is_refused_not_silently_taxed` (PAYE) and `test_non_resident_is_refused` (payroll), are marked `xfail`. They describe the desired behaviour for non-residents, which is not implemented yet, so `pytest` reports them as `xfailed`, not as errors. Remove the marker once non-resident PAYE exists.

---

## 9. Summary of findings

All figures below were worked out by hand and match the test results.

**PAYE at the band edges (resident, monthly):**

| Gross pay (UGX) | PAYE (UGX) |
|---|---|
| 335,000 | 0.00 |
| 335,001 | 0.20 |
| 410,000 | 15,000.00 |
| 485,000 | 33,750.00 |
| 10,000,000 | 2,888,250.00 |
| 10,000,001 | 2,888,250.40 |

Above 10,000,000, each extra shilling is taxed at 40% (30% band rate plus the 10% surcharge).

**Payroll example (gross 1,000,000, no allowances, no Local Service Tax):** NSSF 50,000; PAYE 188,250; net pay 761,750.

**VAT example:** standard-rated sales of 1,000,000 give output VAT of 180,000. Zero-rated and exempt sales add nothing. Standard-rated purchases of 400,000 give input VAT of 72,000. Net VAT payable is 108,000.

**Corporate income tax example:** revenue 50,000,000 minus deductions 20,000,000 gives chargeable income 30,000,000 and tax of 9,000,000. If deductions exceed revenue, the tax is zero.

**Salary versus dividend (1,000,000 each way):** salary nets 761,750 and the dividend nets 850,000, so the dividend leaves 88,250 more in the recipient's hands under the assumed 15% withholding rate.

**Why Decimal and not float:** with floats, `0.1 + 0.2 == 0.3` is `False` and `round(2.675, 2)` gives `2.67` instead of `2.68`. These errors can push a boundary check or a rounding step the wrong way and add up across many payslips. Decimal stores decimal digits exactly.

---

## 10. Limitations

- **Non-resident PAYE** is not implemented, so the residency flag has no effect on PAYE yet. [Remove this line if you implement it.]
- **Local Service Tax is not validated**: a negative amount is accepted, and an amount larger than pay makes PAYE raise `InvalidIncomeError`.
- The **dividend withholding rate (15%)** is an assumption and may differ, for example for dividends from listed companies.
- The planner compares what the **recipient** gets. It ignores that a dividend is paid from profit that has already borne 30% corporate tax, while salary is a deductible expense for the company.
- NSSF is treated as a deduction from net pay. It is also a contribution to the person's retirement savings.
- VAT treatment is simplified. It does not handle partial exemption, where input VAT on exempt supplies cannot be claimed.
- Corporate income tax does not carry losses forward to later years.
- All calculations are monthly (PAYE and payroll) or per period (VAT, corporate tax). There is no annualisation.

---

## 11. Reproducibility

- The notebook runs top to bottom with **Kernel → Restart & Run All** without errors. The interactive calculators are off by default, so nothing waits for input.
- The tax engine uses **no random numbers**, so no random seed is needed there.
- `hypothesis` generates test inputs. The property-based tests are set to `derandomize=True`, so repeated runs use the same examples.

---

## 12. Academic integrity and AI use declaration

I used an AI coding assistant, **Claude (Anthropic)**, while working on this project. I used it to:

- explain concepts (type hints, abstract base classes, `Decimal` rounding, dataclasses, properties, `hypothesis`),
- suggest class designs and example code that I then adapted,
- help debug errors such as `NameError` caused by cell order,
- help draft this README and the written answers to the discussion questions.

I ran and tested all code myself, checked the expected values by hand, and wrote the final version of the notebook. I understand the code and can explain any line of it in a viva.

[Edit this section so that it describes exactly how **you** used AI. It must be true.]

---

## 13. Discussion questions

The written answers to both questions are in **section 9 of the notebook** (`project2_tax_engine.ipynb`), including a runnable cell that shows the float failure:

1. **Why is float unsafe for tax computation?** Floats store most decimal numbers as binary approximations, so `0.1 + 0.2 == 0.3` is `False` and `round(2.675, 2)` gives `2.67` instead of `2.68`. `Decimal` stores exact decimal digits.
2. **Where would inheritance be justified, and where was it avoided?** Used for "is a" relationships (every tax is a `Tax`, every scenario is a `Scenario`); avoided for `Money` (wraps a `Decimal`), residency (a value, not a subclass), and `Payroll` (composition). See section 6.5.
