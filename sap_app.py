### 1st October 2020 ###
## Main Script for handling SAP Online ##


from flask import Flask, request, session, render_template, redirect, url_for, send_file
import pandas as pd
import random

app = Flask(__name__)
"""There are 6 web-pages:
 1) Home Page
 2) Create Journal Entry
 3) Create Lease
 4) View Journal Entries
 5) View Leases
 6) View Financial Statements"""

# Database Info
app.secret_key = 'Hello'

# Pandas Database
je_df = pd.DataFrame({'Date': [], 'Reporting Entity': [], 'Account':[], 'Description': [], 'Amount': []})
lease_df = pd.DataFrame({'Lessor': [], 'Description':[], 'Right-of-Use Asset': [], 'Total Payments': [],'Details': []})
indi_lease = {}

# Leases module
class Leases():
	def __init__(self, name, cashflows, rate, lessor):
		self.name = name
		self.cashflows = cashflows
		self.rate = rate
		self.leaseliability = self.discount()
		self.rou = self.leaseliability
		self.depreciation, self.depreciatedrou = self.depreciate()
		self.amortizedbal, self.interestexp = self.amortize()
		self.payments = self.pay()
		self.lessor = lessor

	def discount(self):
		df = []
		counter = 1
		for item in self.cashflows:
			disc = item / ((1 + self.rate) ** (counter))
			counter = counter + 1
			df.append(disc)
		df2 = sum(df)
		return round(df2, 2)

	def depreciate(self):
		roubal = round(self.rou,2)
		t_roubal = [roubal]
		n = len(self.cashflows)
		depreciation = [0]
		d = self.rou / n
		for item in self.cashflows:
			depreciation.append(d)
		for item in self.cashflows:
			roubal = roubal - depreciation[1]
			t_roubal.append(roubal)
		depreciation = [round(x,2) for x in depreciation]
		t_roubal = [round(x, 2) for x in t_roubal]
		return depreciation,t_roubal

	def amortize(self):
		x = 0
		bal = self.leaseliability
		t_int = [0]
		t_bal = [self.leaseliability]
		for item in self.cashflows:
			int = bal * self.rate
			t_int.append(int)
			bal = bal + int - self.cashflows[x]
			x = x + 1
			t_bal.append(bal)
		t_int = [round(x, 2) for x in t_int]
		t_bal = [round(x,2) for x in t_bal]
		return t_bal, t_int

	def pay(self):
		p = self.cashflows.copy()
		p.insert(0,0)
		p = [round(x,2) for x in p]
		return p

	def prepare(self):
		import pandas as pd
		self.rightofuse = pd.Series(self.depreciatedrou, name="Right-Of-Use Asset")
		self.depreciation = pd.Series(self.depreciation, name="Depreciation")
		self.leaseliability = pd.Series(self.amortizedbal, name="Lease Liability")
		self.interest = pd.Series(self.interestexp, name="Interest Expense")
		self.payments1 = pd.Series(self.payments, name="Payments")
		self.df_final = pd.concat([self.rightofuse, self.depreciation, self.leaseliability, self.interest, self.payments1], axis=1)
		return self.df_final

	def excel(self):
		import pandas as pd
		rightofuse = pd.Series(self.depreciatedrou, name="Right-Of-Use Asset")
		depreciation = pd.Series(self.depreciation, name="Depreciation")
		leaseliability = pd.Series(self.amortizedbal, name="Lease Liability")
		interest = pd.Series(self.interestexp, name="Interest")
		payments = pd.Series(self.payments, name="Payments")
		df = pd.concat([rightofuse, depreciation, leaseliability, interest, payments], axis=1)
		return df.to_excel("Lease Information.xlsx")

n1 = ""
lr1 = ""
a1 = 0
f1 = 0.0

# Start of Routes

@app.route("/")
def welcome():
	return render_template('index.html')

@app.route("/createJE", methods=['GET', 'POST'])
def create_je():
	global je_df
	if request.method == 'POST':
		if request.form['debit'] in ['Asset', 'Purchases', 'Operating Expense']:
			je_df.loc[len(je_df)] = [request.form['date'], request.form['entity'], request.form['debit'], request.form['desc'], float(request.form['amt'])]
			je_df.loc[len(je_df)] = [request.form['date'], request.form['entity'], request.form['credit'], request.form['desc'], (float(request.form['amt'])*-1)]
		else:
			je_df.loc[len(je_df)] = [request.form['date'], request.form['entity'], request.form['debit'], request.form['desc'], (float(request.form['amt'])*-1)]
			je_df.loc[len(je_df)] = [request.form['date'], request.form['entity'], request.form['credit'], request.form['desc'], float(request.form['amt'])]
		return redirect(url_for('success_je'))
	else:
		return render_template('newrecord2.html')

@app.route("/success", methods=['GET', 'POST'])
def success_je():
	return render_template('successful.html')

@app.route("/createLease", methods=['GET', 'POST'])
def create_lease():
	session['usr'] = "user"
	if request.method == 'POST':
		global n1, lr1, a1, f1, indi_lease
		aa = request.form['amt']
		a1 = list(aa.split(","))
		a1 = [float(x) for x in a1]
		f1 = float(request.form['rate'])
		n1 = request.form['leasename']
		lr1 = request.form['lessor']
		lease1 = Leases(n1, a1, f1, lr1)
		indi_lease[request.form['leasename']] = lease1.prepare()
		lease_df.loc[len(lease_df)] = [request.form['lessor'],
									   request.form['leasename'],
									   lease1.rou,
									   sum(a1),
									   f"<a href='{request.form['leasename']}'>{request.form['leasename']}</a>"]

		return redirect(url_for('success_lease'))
	else:
		return render_template('newlease.html')

@app.route("/successlease", methods=['GET', 'POST'])
def success_lease():
	return render_template('successful2.html')

@app.route("/viewJE")
def view_JE():
	return render_template('viewrecords.html', je_table=je_df)

@app.route("/viewLease")
def view_Lease():
	global lease_df
	return render_template('viewleases.html', lease_table=lease_df)

@app.route("/<id>")
def view_iLease(id):
	return render_template('viewleases2.html', lease_table=indi_lease[id], id=id)

@app.route("/viewFS")
def view_FS():
	global je_df
	global m_df
	m_df = je_df.groupby(['Account']).sum().reset_index()
	m_df = m_df[['Account', 'Amount']]
	return render_template('viewFS.html', table=m_df)

@app.route("/downloadje")
def download_journals():
	try:
		a = random.randint(1,100)
		je_df.to_excel(f'static/journals_{a}.xlsx')
		return send_file(f'static/journals_{a}.xlsx', as_attachment=True)
	except Exception as e:
		return str(e)

@app.route("/downloadlease/<gid>/")
def download_lease(gid):
	try:
		indi_lease[gid].to_excel(f'static/{gid}_lease.xlsx')
		return send_file(f'static/{gid}_Lease.xlsx', as_attachment=True)
	except Exception as e:
		return str(e)

@app.route("/downloadleases")
def download_leases():
	try:
		a = random.randint(0,100)
		lease_df.to_excel(f'static/{a}_leases.xlsx')
		return send_file(f'static/{a}_leases.xlsx', as_attachment=True)
	except Exception as e:
		return str(e)

@app.route("/downloadfs")
def download_fs_():
	try:
		a = random.randint(0,100)
		m_df.to_excel(f'static/accounts_{a}.xlsx')
		return send_file(f'static/accounts_{a}.xlsx', as_attachment=True)
	except Exception as e:
		return str(e)

if __name__ == "__main__":
	app.run()
