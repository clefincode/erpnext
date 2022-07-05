// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Instructor Attendance', {
	onload : function(frm){
		frm.set_query('instructor',function(){
		   let lis = null ;
		   frappe.call(
		  {
			  method : 'get_instructor_names',
		   args :{
			   'student_group' : frm.doc.student_group
		   },
		  callback : function(res) {
		   console.log(res.message);
		   lis = res.message;
		   },
		   async : false
		   });
		   return {
			   'filters' : [['Instructor','name','in', lis.join(',')]]
		   };
	   });
   },
	   time_in : function(frm){get_time_difference(frm)},
	   time_out: function (frm) {get_time_difference(frm)}

});
function get_time_difference(frm) {
		frappe.call({
			method : 'get_difference',
			doc: frm.doc,
			callback: function(res){
				frm.set_value('count_of_hours',res.message);
			}
		});
}



