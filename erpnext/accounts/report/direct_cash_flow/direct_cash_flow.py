# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, add_to_date
from erpnext.accounts.report.financial_statements import (get_period_list, get_columns)
from erpnext.accounts.utils import get_fiscal_year, get_balance_on
from six import iteritems


def execute(filters=None):
	period_list = get_period_list(filters.from_fiscal_year, filters.to_fiscal_year,
		filters.period_start_date, filters.period_end_date, filters.filter_based_on,
		filters.periodicity, company=filters.company)

	cash_flow_accounts = get_cash_flow_accounts()
	data = []
	summary_data = {}
	company_currency = frappe.get_cached_value('Company',  filters.company,  "default_currency")
	data.append({
		"account_type": "Cash Flow from Operations",
		"parent_account": None,
		"indent": 0.0,
		"account": "Cash Flow from Operations"
	})
	#operation
	section_data = []
	receivable_data = get_account_type_based_data(filters.company,
		"Receivable", period_list, filters.accumulated_values, filters)
	income_data = get_account_type_based_data(filters.company,
		"Income Account", period_list, filters.accumulated_values, filters)
	
	for key in receivable_data:
		receivable_data[key] += income_data[key]

	receivable_data.update({
		"account_name": "Cash Receipt from Customer",
		"account": "Cash Receipt from Customer",
		"indent": 1,
		"parent_account": "Cash Flow from Operations",
		"currency": company_currency
	})
	data.append(receivable_data)
	section_data.append(receivable_data)

	#--------------------------------------------
	payable_data = get_account_type_based_data(filters.company,
		"Payable", period_list, filters.accumulated_values, filters)
	#Cost of Goods Sold Type
	cogs_data = get_account_type_based_data(filters.company,
		"Cost of Goods Sold", period_list, filters.accumulated_values, filters)
	stock_data = get_account_type_based_data(filters.company,
		"Stock", period_list, filters.accumulated_values, filters)
	#Stock Received But Not Billed
	srbnb = get_account_type_based_data(filters.company,
		"Stock Received But Not Billed", period_list, filters.accumulated_values, filters)
	
	
	for key in payable_data:
		payable_data[key] += cogs_data[key] + stock_data[key] + srbnb[key]

	payable_data.update({
		"account_name": "Cash Paid to Supplier",
		"account": "Cash Paid to Supplier",
		"indent": 1,
		"parent_account": "Cash Flow from Operations",
		"currency": company_currency
	})
	data.append(payable_data)
	section_data.append(payable_data)
	#--------------------------------------
	other_debit_data = get_account_type_based_data(filters.company,
		"Prepaid Expense", period_list, filters.accumulated_values, filters)
	other_credit_data = get_account_type_based_data(filters.company,
		"Accrued Expense", period_list, filters.accumulated_values, filters)
	for key in other_debit_data:
		other_debit_data[key] += other_credit_data[key]
	for type in ["Expense Account", "Round Off", "Expenses Included In Valuation", "Chargeable", "Stock Adjustment"]:
		minus_type = get_account_type_based_data(filters.company,
		type, period_list, filters.accumulated_values, filters)
		for key in other_debit_data:
			other_debit_data[key] += minus_type[key]
	other_debit_data.update({
		"account_name": "Cash Paid to Expense",
		"account": "Cash Paid to Expense",
		"indent": 1,
		"parent_account": "Cash Flow from Operations",
		"currency": company_currency
	})
	data.append(other_debit_data)
	section_data.append(other_debit_data)
	#------------------------------------------
	temporary_data = get_account_type_based_data(filters.company,
		"Temporary", period_list, filters.accumulated_values, filters)
	temporary_data.update({
		"account_name": "Temporary",
		"account": "Temporary",
		"indent": 1,
		"parent_account": "Cash Flow from Operations",
		"currency": company_currency
	})
	data.append(temporary_data)
	section_data.append(temporary_data)

	add_total_row_account(data, section_data, "Net Cash from Operations",
		period_list, company_currency, summary_data, filters) 


	for cash_flow_account in cash_flow_accounts:
		section_data = []
		data.append({
			"account_name": cash_flow_account['section_header'],
			"parent_account": None,
			"indent": 0.0,
			"account": cash_flow_account['section_header']
		})

		for account in cash_flow_account['account_types']:
			account_data = get_account_type_based_data(filters.company,
				account['account_type'], period_list, filters.accumulated_values, filters)
			account_data.update({
				"account_name": account['label'],
				"account": account['label'],
				"indent": 1,
				"parent_account": cash_flow_account['section_header'],
				"currency": company_currency
			})
			data.append(account_data)
			section_data.append(account_data)

		add_total_row_account(data, section_data, cash_flow_account['section_footer'],
			period_list, company_currency, summary_data, filters)

	add_total_row_account(data, data, _("Net Change in Cash"), period_list, company_currency, summary_data, filters)
	start, end = get_account_type_balance_data(["Bank", "Cash"], period_list, filters.company)
	data.append(start)
	data.append(end)
	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, filters.company)

	chart = get_chart_data(columns, data)

	report_summary = get_report_summary(summary_data, company_currency)

	return columns, data, None, chart, report_summary

def get_cash_flow_accounts():

	investing_accounts = {
		"section_name": "Investing",
		"section_footer": _("Net Cash from Investing"),
		"section_header": _("Cash Flow from Investing"),
		"account_types": [
			{"account_type": "Fixed Asset", "label": _("Net Change in Fixed Asset")}
		]
	}

	financing_accounts = {
		"section_name": "Financing",
		"section_footer": _("Net Cash from Financing"),
		"section_header": _("Cash Flow from Financing"),
		"account_types": [
			{"account_type": "Equity", "label": _("Net Change in Equity")}
		]
	}

	# combine all cash flow accounts for iteration
	return [ investing_accounts, financing_accounts]

def get_account_type_based_data(company, account_type, period_list, accumulated_values, filters):
	data = {}
	total = 0
	for period in period_list:
		start_date = get_start_date(period, accumulated_values, company)

		amount = get_account_type_based_gl_data(company, start_date,
			period['to_date'], account_type, filters)

		if amount and account_type == "Depreciation":
			amount *= -1

		total += amount
		data.setdefault(period["key"], amount)

	data["total"] = total
	return data

def get_account_type_based_gl_data(company, start_date, end_date, account_type, filters={}):
	cond = ""
	filters = frappe._dict(filters)

	if filters.include_default_book_entries:
		company_fb = frappe.db.get_value("Company", company, 'default_finance_book')
		cond = """ AND (finance_book in (%s, %s, '') OR finance_book IS NULL)
			""" %(frappe.db.escape(filters.finance_book), frappe.db.escape(company_fb))
	else:
		cond = " AND (finance_book in (%s, '') OR finance_book IS NULL)" %(frappe.db.escape(cstr(filters.finance_book)))


	gl_sum = frappe.db.sql_list("""
		select sum(credit) - sum(debit)
		from `tabGL Entry`
		where company=%s and posting_date >= %s and posting_date <= %s
			and voucher_type != 'Period Closing Voucher'
			and account in ( SELECT name FROM tabAccount WHERE account_type = %s) {cond}
	""".format(cond=cond), (company, start_date, end_date, account_type))

	return gl_sum[0] if gl_sum and gl_sum[0] else 0

def get_start_date(period, accumulated_values, company):
	if not accumulated_values and period.get('from_date'):
		return period['from_date']

	start_date = period["year_start_date"]
	if accumulated_values:
		start_date = get_fiscal_year(period.to_date, company=company)[1]

	return start_date

def add_total_row_account(out, data, label, period_list, currency, summary_data, filters, consolidated=False):
	total_row = {
		"account_name": "'" + _("{0}").format(label) + "'",
		"account": "'" + _("{0}").format(label) + "'",
		"currency": currency
	}

	summary_data[label] = 0

	# from consolidated financial statement
	if filters.get('accumulated_in_group_company'):
		period_list = get_filtered_list_for_consolidated_report(filters, period_list)

	for row in data:
		if row.get("parent_account"):
			for period in period_list:
				key = period if consolidated else period['key']
				total_row.setdefault(key, 0.0)
				total_row[key] += row.get(key, 0.0)
				summary_data[label] += row.get(key)

			total_row.setdefault("total", 0.0)
			total_row["total"] += row["total"]

	out.append(total_row)
	out.append({})


def get_report_summary(summary_data, currency):
	report_summary = []

	for label, value in iteritems(summary_data):
		report_summary.append(
			{
				"value": value,
				"label": label,
				"datatype": "Currency",
				"currency": currency
			}
		)

	return report_summary


def get_chart_data(columns, data):
	labels = [d.get("label") for d in columns[2:]]
	datasets = [{'name':account.get('account').replace("'", ""), 'values': [account.get('total')]}  for account in data if account.get('parent_account') == None and account.get('currency')]
	datasets = datasets[:-1]

	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		},
		"type": "bar"
	}

	chart["fieldtype"] = "Currency"

	return chart

def get_filtered_list_for_consolidated_report(filters, period_list):
	filtered_summary_list = []
	for period in period_list:
		if period == filters.get('company'):
			filtered_summary_list.append(period)

	return filtered_summary_list

def get_account_type_balance_data(account_types, period_list, company):
	start_data = {}
	end_data = {}
	first_period = period_list[0]
	start_total, __ = get_balance_for_period(first_period, company, account_types)
	last_period = period_list[-1]
	__, end_total = get_balance_for_period(last_period, company, account_types)
	
	for period in period_list:
		start_amount, end_amount = get_balance_for_period(period, company, account_types)
		start_data.setdefault(period["key"], start_amount)
		end_data.setdefault(period["key"], end_amount)

	start_data.update({
		"total": start_total,
		"account_name": "Beginning Cash Balance",
		"account": "Beginning Cash Balance"
	})
	end_data.update({
		"total": end_total,
		"account_name": "Ending Cash Balance",
		"account": "Ending Cash Balance"
	})
	return start_data, end_data

def get_balance_for_period(period, company, account_types):
	start_date = add_to_date(get_start_date(period, 0, company), days=-1)
	start_amount = get_balance_for_type(start_date, account_types, company)
	end_amount = get_balance_for_type(period['to_date'], account_types, company)
	return start_amount, end_amount


def get_balance_for_type(date, types, company):
	accounts = frappe.get_all("Account", filters={"account_type": ["in", types], "is_group": 0, "company": company}, pluck="name")
	balance = 0
	for acc in accounts:
		balance += get_balance_on(account=acc, date=date, in_account_currency=False)
	return balance