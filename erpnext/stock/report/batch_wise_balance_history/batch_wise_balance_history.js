// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Batch-Wise Balance History"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			width: "80",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			width: "80",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
			get_query: function () {
				return {
					filters: {
						has_batch_no: 1,
					},
				};
			},
		},
		{
			fieldname: "warehouse_type",
			label: __("Warehouse Type"),
			fieldtype: "Link",
			width: "80",
			options: "Warehouse Type",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			get_query: function () {
				let warehouse_type = frappe.query_report.get_filter_value("warehouse_type");
				let company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						...(warehouse_type && { warehouse_type }),
						...(company && { company }),
					},
				};
			},
		},
		{
			fieldname: "batch_no",
			label: __("Batch No"),
			fieldtype: "Link",
			options: "Batch",
			get_query: function () {
				let item_code = frappe.query_report.get_filter_value("item_code");
				return {
					filters: {
						item: item_code,
					},
				};
			},
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		
		if (column.fieldname == "Batch" && data && !!data["Batch"]) {
			value = data["Batch"];
			column.link_onclick =
				"frappe.query_reports['Batch-Wise Balance History'].set_batch_route_to_stock_ledger(" +
				JSON.stringify(data) +
				")";
		}

		if (column.fieldname == "valuation_rate" && data) {
				if (data.item && data.warehouse && data.batch && !data.valuation_rate_fetching) {
					data.valuation_rate_fetching = true;

					frappe.call({
						method: "kensingtonbn.www.api.api.fetch_valuation_rate",
						args: {
							item_code: data.item,
							warehouse: data.warehouse,
							batch_no: data.batch,
						},
						callback: function (r) {
							if (r.message !== undefined && data.valuation_rate!=r.message) {
								data.valuation_rate = r.message;
								data.valuation_rate_fetched = true;
								frappe.query_report.datatable.refresh();
							}
						
						},
					});
				}
			if (data.valuation_rate != null) {
				value = format_currency(data.valuation_rate, frappe.defaults.get_default("currency"));
			}
		}
		if (column.fieldname == "last_purchase_rate" && data) {
			if (data.item && !data.last_purchase_rate_fetching) {
				data.last_purchase_rate_fetching = true;
	
				frappe.call({
					method: "kensingtonbn.www.api.api.fetch_last_purchase_rate",
					args: {
						item_code: data.item,
					},
					callback: function (r) {
						if (r.message !== undefined && data.last_purchase_rate != r.message) {
							data.last_purchase_rate = r.message;
							data.last_purchase_rate_fetched = true;
							frappe.query_report.datatable.refresh();
						}
					},
				});
			}
			if (data.last_purchase_rate != null) {
				value = format_currency(data.last_purchase_rate, 'BND');
			}
		}

		value = default_formatter(value, row, column, data);
		return value;
	},

	set_batch_route_to_stock_ledger: function (data) {
		frappe.route_options = {
			batch_no: data["Batch"],
		};
		frappe.set_route("query-report", "Stock Ledger");
	},
};