// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var datatable = null
var rows = null
frappe.ui.form.on('Student Group Evaluation Tool', {
	student_group: function(frm){
		frappe.call({
			method: "get_student_group_data",
			doc: frm.doc,
			callback: function(r){
				rows = r.message[1] ;
				for(var i=0 ; i< r.message[1].length; i++){
					if(r.message[1][i].question.avg == 1){
						r.message[1][i].question.format = function(value){
							return value.fontcolor('red');
						}	
					}
				}
				datatable = new frappe.DataTable("#exee",{
					columns: r.message[0],
					data: r.message[1],
					getEditor(colIndex, rowIndex, value, parent, column, row, data){
						const $input = document.createElement('input');
						$input.type = 'text';
						parent.appendChild($input);

						return {
							// called when cell is being edited
							initValue(value) {
								$input.focus();
								$input.value = "";
							},
							// called when cell value is set
							setValue(value) {
								$input.value = value;
								rows[rowIndex][column.id] = value;
							},
							// value to show in cell
							getValue() {
								return $input.value;
							}
						}
					},
					dynamicRowHeight: 1
				});
				if (r.message[2] == false)
					frm.events.submit_results(frm);
			}
		})
	},
	refresh: function(frm){
		frm.disable_save();
	},
	submit_results: function(frm){
		frm.page.set_primary_action("Submit", function(){
			frappe.call({
				method: "create_student_group_evaluations",
				doc: frm.doc,
				args: {
					'data': rows
				},
				callback: function(r){
					frappe.msgprint("Evaluations Created");
					frm.page.clear_primary_action();
					frm.trigger("student_group");
				}
			});
		});
	}
});
