import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
#from streamlit_extras.metric_cards import style_metric_cards
import warnings
from io import StringIO
import boto3
import datetime

# Disable warnings
warnings.filterwarnings('ignore')

# Configure Streamlit page
st.set_page_config(page_title="Dashboard", page_icon=":chart_with_upwards_trend:", layout="wide")

# Custom CSS styling
st.markdown(
    """
    <style>
    body { background-color: #ffffff; }
    [data-testid=metric-container] { box-shadow: 0 0 4px #686664; padding: 10px; }
    .plot-container>div { box-shadow: 0 0 2px #070505; padding: 5px; border-color: #000000; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 1.2rem; color: rgb(0, 0, 0); border-color: #000000; }
    .sidebar-content { color: white; }
    [data-testid=stSidebar] { color: white; }
    </style>
    """,
    unsafe_allow_html=True
)

# Class definition for the dashboard
class Dashboard:
    def __init__(self, data):
        self.data = data
        self.df = pd.read_csv(StringIO(self.data))
        self.df["created"] = pd.to_datetime(self.df["created"])
    #def style_metric_cards(self, background_color="#333333", border_left_color="#444444", border_color="#555555", box_shadow="#000000"):
        st.markdown(
            f"""
            <style>
            div[data-testid="metric-container"] {{
                background-color: #333333;
                border-left: 5px solid #444444;
                border: 1px solid #555555;
                box-shadow: 0 0 4px #000000;
                padding: 10px;
                border-radius: 5px;
                color: #FFFFFF;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
    

    def revenue(self):
        df_selection = self._get_filtered_data()
        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
    

        with st.expander("VIEW DATA"):
            showData = st.multiselect('Filter: ', df_selection.columns, default=[
                'created', 'customer_id', 'email', 'phone', 'name',  'subscription', 'invoice_number',
                'description', 'quantity', 'currency', 'line_item_amount',
                'total_invoice_amount', 'discount', 'fee', 'tax', 'net_amount'
            ])
            st.dataframe(df_selection[showData], use_container_width=True)

        total_amount = df_selection['total_invoice_amount'].sum()
        total_transactions = df_selection["total_invoice_amount"].count() # Total transaction
        total_net_amount = df_selection["net_amount"].sum() # Total net Amount
        total_fee_amount = df_selection["fee"].sum() # Total fee amount
        total_subscriptions_sold = df_selection.dropna(subset=["subscription"]).shape[0] # Total subscriptions sold (monthly, yearly)
        total_tax = df_selection["tax"].sum() # Total tax

        # Display metrics
        self._display_metrics(total_tax, total_net_amount, total_fee_amount, total_transactions, total_subscriptions_sold, total_amount)

        # Visualizations
        self._create_charts(df_selection)

    #self.style_metric_cards()

    def _get_filtered_data(self):
        start_date = st.sidebar.date_input("Start date", self.df["created"].min())
        end_date = st.sidebar.date_input("End date", self.df["created"].max())

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        return self.df.query("created >= @start_date and created <= @end_date")

    def _display_metrics(self, total_tax, total_net_amount, total_fee_amount, total_transactions, total_subscriptions_sold, total_amount):
        total1, total2, total3 = st.columns(3, gap='small')
        
        with total1:
            st.info('Total Amount',  icon="💰")
            st.metric(label="Total Amount", value=f"$ {total_amount:,.0f}")

        with total2:
            st.info('Total Tax Amount', icon="💸")
            st.metric(label="Total Tax", value=f"$ {total_tax:,.0f}")

        with total3:
            st.info('Total Net Amount', icon="📊")
            st.metric(label="Total Net Amount", value=f"$ {total_net_amount:,.0f}")
        

        total1, total2, total3 = st.columns(3, gap='small')

        with total1:
            st.info('Total Fee Amount', icon="💼")
            st.metric(label="Total Fee Amount", value=f"$ {total_fee_amount:,.0f}")

        with total2:
            st.info('Total Transactions', icon="🧾")
            st.metric(label="Total Transactions", value=f"{total_transactions:,}")

        with total3:
            st.info('Subscriptions Sold', icon="📦")
            st.metric(label="Total Subscriptions Sold", value=f"{total_subscriptions_sold:,}")
        

    def _create_charts(self, df_selection):
        df_selection['year_month'] = df_selection['created'].dt.to_period('M')

        # Group by 'year_month' and sum the 'net_amount'
        monthly_net_amount = df_selection.groupby('year_month')['net_amount'].sum().reset_index()
        monthly_net_amount['year_month'] = monthly_net_amount['year_month'].astype(str)
        fig = px.bar(monthly_net_amount, x='year_month', y='net_amount', title="Total Net Amount by Month",
                    labels={'year_month': 'Month', 'net_amount': 'Total Net Amount ($)'})
        
        # Group by 'year_month' and sum the 'tax'
        monthly_tax = df_selection.groupby('year_month')['tax'].sum().reset_index()
        monthly_tax['year_month'] = monthly_tax['year_month'].astype(str)
        fig_2 = px.pie(monthly_tax, values='tax', names='year_month', title="Total Tax by Month",
                    labels={'year_month': 'Month', 'tax': 'Total Tax ($)'})

        total1, total2 = st.columns(2, gap='small')
        with total1:
            st.plotly_chart(fig)

        with total2:
            st.plotly_chart(fig_2)

        df_selection['total_invoice_amount'] = df_selection['total_invoice_amount'].astype(int)
        top_customers = df_selection.groupby('customer_id')['total_invoice_amount'].sum().reset_index()
        top_customers = top_customers.sort_values(by='total_invoice_amount', ascending=False).head(10)
        fig = px.bar(top_customers, x='customer_id', y='total_invoice_amount', title='Top 10 Customers by Revenue')
        st.plotly_chart(fig)

        with st.expander("VIEW DATA"):
            st.dataframe(top_customers)

        revenue_by_product = df_selection.groupby('description')['total_invoice_amount'].sum().reset_index()
        # Sort the values and get the top 10
        top_revenue_by_product = revenue_by_product.sort_values(by='total_invoice_amount', ascending=False).head(10)
        # Create the treemap visualization
        fig = px.treemap(top_revenue_by_product, path=['description'], values='total_invoice_amount', title='Top 10 Products by Revenue')
        st.plotly_chart(fig)

        with st.expander("VIEW DATA"):
            st.dataframe(top_revenue_by_product)

        df_selection['month'] = df_selection['created'].dt.to_period('M').astype(str)
        tax_fee = df_selection.groupby('month').agg({'tax': 'sum', 'fee': 'sum'}).reset_index()
        fig = px.bar(tax_fee, x='month', y=['tax', 'fee'], title='Tax and Fee Analysis Over Time')
        st.plotly_chart(fig)

        with st.expander("VIEW DATA"):
            st.dataframe(tax_fee)

        subscription_analysis = df_selection['subscription'].value_counts().reset_index()
        subscription_analysis.columns = ['Subscription', 'Count']
        fig = px.bar(subscription_analysis, x='Subscription', y='Count', title='Revenue by Subscription')
        st.plotly_chart(fig)

        with st.expander("VIEW DATA"):
            st.dataframe(subscription_analysis)
    def Customers(*args):
        # Load customer data from the customers.csv file
        s3_client = boto3.client('s3')
        response2 = s3_client.get_object(Bucket='stripe-raw-data-dashboard', Key='customers_6months.csv')
        content2 = response2['Body'].read().decode('utf-8')
        customers= pd.read_csv(StringIO(content2))

        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
    

        st.sidebar.header("Select Date Range:")
        customers['created'] = pd.to_datetime(customers['created'], errors='coerce')

        start_date = st.sidebar.date_input("Start date", customers["created"].min().date())
        end_date = st.sidebar.date_input("End date", customers["created"].max().date())

        # Filter data
        filtered_df = customers[(customers['created'] >= pd.to_datetime(start_date)) & (customers['created'] <= pd.to_datetime(end_date))]

        # Customer churn analysis
        st.subheader("Customer Retention and Churn Analysis")
        total_customers = filtered_df.shape[0]
        churned_customers = filtered_df['deleted'].sum()  # Assuming 'deleted' is a boolean for churned customers
        churn_rate = churned_customers / total_customers * 100
        
        # Display churn rate in metrics
        # st.metric("Total Customers", total_customers)
        # st.metric("Churned Customers", churned_customers)
        # st.metric("Churn Rate", f"{churn_rate:.2f}%")

        # total1, total2, total3 = st.columns(3, gap='small')
        # with total1:
        st.info('Total Customers')
        st.metric(label="Total Customers", value=f" {total_customers:,.0f}")

        # with total2:
        #     st.info('Churned Customers')
        #     st.metric(label="Churned Customers", value=f"{churned_customers:.2f}")

        # with total3:
        #     st.info('Churn Rate')
        #     st.metric(label="Churn Rate", value=f"{churn_rate:.2f}%")
        
        with st.expander("VIEW DATA"):
            filtered_df['created'] = pd.to_datetime(filtered_df['created']).dt.date

            showData = st.multiselect('Filter: ', filtered_df.columns, default=[
                'created',  'email', 'phone', 'name',"address_country"])
            st.dataframe(filtered_df[showData], use_container_width=True)


        # Convert 'created' to datetime if it's not already
        customers['created'] = pd.to_datetime(customers['created'])

        # Filter data for the last 6 months
        current_date = pd.to_datetime("today")
        start_date = current_date - pd.DateOffset(months=6)
        filtered_customers = customers[customers['created'] >= start_date]

        # Group by month and count new customers
        filtered_customers.set_index('created', inplace=True)
        monthly_new_customers = filtered_customers.resample('M').size().reset_index(name='new_customers_count')

        # Correctly align data with the months
        monthly_new_customers['year_month'] = monthly_new_customers['created'].dt.strftime('%Y-%m')

        # Sort by 'year_month' in ascending order
        monthly_new_customers = monthly_new_customers.sort_values(by='created', ascending=True)

        st.subheader('New Customer Sign-Up Trend')

        # Plot the data
        fig = px.bar(
            monthly_new_customers,
            x='year_month',
            y='new_customers_count',
            title="New Customer Sign-Ups by Month",
            width=1200,
            height=400,
            color_discrete_sequence=['#636EFA']
        )

        fig.update_layout(
            xaxis_title='Month',
            yaxis_title='New Customers Count',
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1
        )

        st.plotly_chart(fig)

        
        # Filter data for the last 6 months
        df_sign_up = filtered_df[["id", "created"]]
        df_sign_up["created"] = pd.to_datetime(df_sign_up["created"])
        df_sign_up["Month_year"] = df_sign_up["created"].dt.strftime('%Y-%m')
        df_sign_up = df_sign_up[["id", "Month_year"]]
        df_sign_up["Cust_count_month"] = df_sign_up.groupby("Month_year")["id"].transform('count')
        df_sign_up_data = df_sign_up[["Month_year", "Cust_count_month"]]
        df_sign_up_data = df_sign_up_data.drop_duplicates()
        df_sign_up_data = df_sign_up_data.sort_values(by=['Month_year'], ascending=False)
        df_sign_up_data.reset_index(drop=True, inplace=True)
        with st.expander("VIEW DATA"):
            st.dataframe(df_sign_up_data) #, use_container_width=True
                
    
        geo_data = filtered_df[['shipping_address_city', 'shipping_address_country']].dropna()
        city_counts = geo_data['shipping_address_city'].value_counts().reset_index()
        city_counts.columns = ['City', 'Count']

        fig = px.bar(city_counts.head(10), x='City', y='Count', title='Top 10 Cities by Customer Count')
        st.plotly_chart(fig)
    
#################################################################################################
        



        # Display an interactive table
        city_counts = filtered_df['shipping_address_city'].value_counts().reset_index()
        city_counts.columns = ['City', 'Count']
        with st.expander("VIEW DATA"):
            st.dataframe(city_counts)

        # Prepare data for the donut chart
        country_counts = filtered_df['shipping_address_country'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Count']

        fig = px.pie(country_counts.head(5), values='Count', names='Country', title='Top 5 Countries by Customer Count', hole=0.4)

        fig.update_traces(textinfo='percent+label')
        fig.update_layout(annotations=[dict(text='Countries', x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.plotly_chart(fig)




    def subscriptions(*args):
        s3_client = boto3.client('s3')
        response1 = s3_client.get_object(Bucket='stripe-raw-data-dashboard', Key='subscriptions_6months.csv')
        response2= s3_client.get_object(Bucket='stripe-raw-data-dashboard', Key='customers_6months.csv')
        content1 = response1['Body'].read().decode('utf-8')
        content2 = response2['Body'].read().decode('utf-8')
        df_sub = pd.read_csv(StringIO(content1))
        df_cust =  pd.read_csv(StringIO(content2))

        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
    

        # # Ensure the 'created' and 'current_period_end' columns are in datetime format
        # df3['created'] = pd.to_datetime(df3['created'], errors='coerce')
        # df3['current_period_end'] = pd.to_datetime(df3['current_period_end'], errors='coerce')


        # Convert 'trial_end' and 'created' to datetime
        df_sub['trial_end'] = pd.to_datetime(df_sub['trial_end'])
        df_sub['created'] = pd.to_datetime(df_sub['created'])

        # Sidebar filter for date range
        st.sidebar.header("Select Date Range:")
        start_date = st.sidebar.date_input("Start date", datetime.date.today() - datetime.timedelta(days=30))
        end_date = st.sidebar.date_input("End date", datetime.date.today())
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter the subscription data
        df_sub_end = df_sub[(df_sub["trial_end"] >= start_date) & (df_sub["trial_end"] <= end_date)]
        df_cust_sub_end = df_sub_end.merge(df_cust, left_on="customer_id", right_on="id", how="inner")


        # # Active Subscriptions
        # st.subheader("Active Subscriptions")

        
        # Select relevant columns for analysis
        df_sub_ch = df_sub[["customer_id", "trial_start", "trial_end", "status", "start_date"]]
        # Calculate the total number of active and inactive subscriptions
        total_active = df_sub_end[df_sub_end["status"] == "active"].shape[0]
        total_inactive = df_sub_end[df_sub_end["status"] != "active"].shape[0]
        total_trialing = df_sub_end[df_sub_end["status"] == "trialing"].shape[0]
        total_past_due = df_sub_end[df_sub_end["status"] == "past_due"].shape[0]
        total_paused = df_sub_end[df_sub_end["status"] == "paused"].shape[0]
        total_incomplete_expired = df_sub_end[df_sub_end["status"] == "incomplete_expired"].shape[0]
        

        # Create columns in Streamlit
        total1, total2, total3 = st.columns(3, gap='small')

        # Display total active and inactive subscriptions in the columns
        with total1:
            st.info('Active Subscriptions')
            st.metric(label="Total Active Subscriptions", value=str(total_active))

        with total2:
            st.info('Inactive Subscriptions')
            st.metric(label="Total Inactive Subscriptions", value=str(total_inactive))
        
        with total3:
            st.info('Trialing Subscriptions')
            st.metric(label="Total trialing Subscriptions", value=str(total_trialing))
        
        # Create columns in Streamlit
        total1, total2, total3 = st.columns(3, gap='small')

        # Display total active and inactive subscriptions in the columns
        with total1:
            st.info('Past Due Subscriptions')
            st.metric(label="Past Due Subscriptions", value=str(total_past_due))

        with total2:
            st.info('Paused Subscriptions')
            st.metric(label="Total Paused Subscriptions", value=str(total_paused))
        
        with total3:
            st.info('Incomplete Expired Subscriptions')
            st.metric(label="Total Incomplete Expired Subscriptions", value=str(total_incomplete_expired))

        # Display upcoming subscription end customers
        st.subheader("Upcoming Subscription End Customers")
        with st.expander("VIEW DATA"):
            df_cust_sub_end['trial_start'] = pd.to_datetime(df_sub['trial_start']).dt.date
            df_cust_sub_end['trial_end'] = pd.to_datetime(df_sub['trial_end']).dt.date
            showData = st.multiselect('Filter: ', df_cust_sub_end.columns, default=[
                "name", "phone", "email", "trial_start","trial_end"])
            st.dataframe(df_cust_sub_end[showData], use_container_width=True)
        # st.dataframe(df_cust_sub_end[["name", "phone", "email", "trial_end"]])    

        # Get the value counts of the 'status' column
        status_counts = df_sub_end["status"].value_counts()

        # Create a bar chart using Plotly
        fig = px.bar(x=status_counts.index, y=status_counts.values,
                    title="Subscription Status Distribution",
                    labels={'x': 'Subscription Status', 'y': 'Count'})

        # Display the bar chart in the Streamlit app
        st.plotly_chart(fig)


        # Monthly Active Subscriptions
        df_sub_end["month"] = df_sub_end["created"].dt.to_period('M').astype(str)
        monthly_active_subs = df_sub_end.groupby("month")["customer_id"].count().reset_index()
        fig_monthly = px.bar(monthly_active_subs, x="month", y="customer_id", title="Monthly Active Subscriptions")
        st.plotly_chart(fig_monthly)

        # Daily Active Subscriptions
        df_sub_end["day"] = df_sub_end["created"].dt.strftime('%Y-%m-%d')
        daily_active_subs = df_sub_end.groupby("day")["customer_id"].count().reset_index()
        fig_daily = px.bar(daily_active_subs, x="day", y="customer_id", title="Daily Active Subscriptions")
        fig_daily.update_layout(
            xaxis_title='Date',
            yaxis_title='Number of Active Subscriptions',
            xaxis_tickformat='%Y-%m-%d'
        )
        st.plotly_chart(fig_daily)

        
        # customer_id = "cus_OzTLZG52Io2Izb"
        # customer_data = df_sub_end[df_sub_end["customer_id"] == customer_id]

        # # Get the value counts of the 'status' column for the specific customer
        # status_counts = customer_data["status"].value_counts()

        # # Create a bar chart using Plotly to display the customer's subscription status distribution
        # fig = px.bar(x=status_counts.index, y=status_counts.values,
        #             title=f"Subscription Status Distribution for Customer {customer_id}",
        #             labels={'x': 'Subscription Status', 'y': 'Count'})

        # # Display the bar chart in the Streamlit app
        # st.plotly_chart(fig)

        # Filter the data for the specific customer_id
        df_sub_end['trial_start'] = pd.to_datetime(df_sub_end['trial_start']).dt.date
        df_sub_end['trial_end'] = pd.to_datetime(df_sub_end['trial_end']).dt.date
        df_sub_end[df_sub_end["customer_id"]=="cus_OzTLZG52Io2Izb"][["customer_id","trial_start","trial_end","status"]].sort_values(by=["trial_start"])
        with st.expander("VIEW DATA"):
            st.dataframe(df_sub_end[df_sub_end["customer_id"]=="cus_OzTLZG52Io2Izb"][["customer_id","trial_start","trial_end","status"]].sort_values(by=["trial_start"]), use_container_width=True)

        
        # Count the number of times each customer has used the trial
        df_trial_counts = df_sub_end["customer_id"].value_counts().reset_index()
        df_trial_counts.columns = ['customer_id', 'trial_count']

        # Filter customers who have used the trial multiple times (e.g., more than once)
        df_multiple_trials = df_trial_counts[df_trial_counts['trial_count'] > 1]

        # Display the title in the Streamlit app
        st.subheader("Customers Who Used Trial Multiple Times")

        # Check if there are any customers with multiple trials
        if not df_multiple_trials.empty:
            
            st.bar_chart(df_multiple_trials.set_index('customer_id')['trial_count'])

            with st.expander("VIEW DATA"):
                st.dataframe(df_multiple_trials)
        else:
            st.write("No customers have used the trial multiple times.")

        



    def payment(self):
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket='stripe-raw-data-dashboard', Key='both_success_fail.csv')
        content = response['Body'].read().decode('utf-8')
        payment_df = pd.read_csv(StringIO(content))

        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
        
        st.sidebar.header("Select Date Range:")
        payment_df['created_date'] = pd.to_datetime(payment_df['created_date'], errors='coerce')

        start_date = st.sidebar.date_input("Start date", payment_df["created_date"].min().date())
        end_date = st.sidebar.date_input("End date", payment_df["created_date"].max().date())

        # Filter data
        df2_filtered  = payment_df[(payment_df['created_date'] >= pd.to_datetime(start_date)) & (payment_df['created_date'] <= pd.to_datetime(end_date))]


        if df2_filtered.empty:
            st.error("No data available for the selected date range.")
            return
        

        with st.expander("VIEW DATA"):
            df2_filtered['created_date'] = pd.to_datetime(df2_filtered['created_date']).dt.date
            showData = st.multiselect('Filter: ', df2_filtered.columns, default=[
                'id', 'amount', 'amount_refunded', 'balance_transaction_id',
                'calculated_statement_descriptor',  'created_date', 'currency', 'customer_id',
                'description', 'status'])
            st.dataframe(df2_filtered[showData], use_container_width=True)

        total_transactions = df2_filtered.shape[0]
        successful_transactions = df2_filtered[df2_filtered["status"] == "succeeded"].shape[0]
        failed_transactions = df2_filtered[df2_filtered["status"] == "failed"].shape[0]

        total1, total2, total3 = st.columns(3, gap='small')
        with total1:
            st.info('Total Transactions')
            st.metric(label="Total Transactions", value=f" {total_transactions:,.0f}")

        with total2:
            st.info('Number of successful transactions')
            st.metric(label="Number of successful transactions:", value=f"{successful_transactions:,.0f}")

        with total3:
            st.info('Number of failed transactions')
            st.metric(label="Number of failed transactions:", value=f"{failed_transactions:,.0f}")

        st.markdown("---")

        total1, total2 = st.columns(2, gap='small')
        with total1:
            refunded_line_items = df2_filtered[df2_filtered["refunded"] == True]["description"].value_counts()
            top_2 = refunded_line_items.head(2)
            other = refunded_line_items[2:].sum() if len(refunded_line_items) > 2 else 0
            top_2_with_other = pd.concat([top_2, pd.Series({'Other': other})])

            fig = px.pie(values=top_2_with_other, names=top_2_with_other.index, title="Top 2 Refunded Line Items and Others",
                        labels={'index': 'Refunded Items', 'values': 'Count'}, hole=0.3)
            st.plotly_chart(fig)

        with total2:
            status_counts = df2_filtered['status'].value_counts()
            
            if not status_counts.empty and 'succeeded' in status_counts and 'failed' in status_counts:
                succeeded_count = status_counts['succeeded']
                failed_count = status_counts['failed']
                
                # Prepare the data for the pie chart
                labels = ['Succeeded', 'Failed']
                values = [succeeded_count, failed_count]
                
                # Create a Plotly pie chart for payment statuses
                fig = px.pie(values=values, names=labels, title="Payment Status Distribution",
                            labels={'index': 'Payment Status', 'values': 'Count'}, hole=0.3)
                st.plotly_chart(fig)
            else:
                st.write("No data available for succeeded or failed payments.")

        failure_reasons = (df2_filtered["failure_code"].value_counts(normalize=True).head() * 100).round(2)
        failure_reasons_df = failure_reasons.reset_index()
        failure_reasons_df.columns = ['Failure Reason', 'Percentage']
        fig = px.bar(
            failure_reasons_df, 
            x='Failure Reason', 
            y='Percentage',
            title="Top 5 Failure Reasons",
            labels={'Failure Reason': 'Failure Reason', 'Percentage': 'Percentage (%)'},
            text='Percentage',
            width=800,  # Adjusted width
            height=600
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(
            xaxis_title='Failure Reason', 
            yaxis_title='Percentage (%)', 
            xaxis_tickangle=320,
            margin=dict(l=20, r=20, t=40, b=20),  # Adjust margins if needed
        )
        st.plotly_chart(fig)


        refunded_amounts = df2_filtered[df2_filtered["amount_refunded"] > 0]["amount_refunded"].value_counts().head()
        st.subheader("Most Frequent Refunded Amounts")
        st.bar_chart(refunded_amounts,x_label="Amount Refunded", y_label="Count")

    def financial(self):
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket='stripe-raw-data-dashboard', Key='financial.csv')
        content = response['Body'].read().decode('utf-8')
        financial_df = pd.read_csv(StringIO(content))
        st.markdown(
                """
                <style>
                [data-testid="stElementToolbar"] {
                    display: none;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

        # Sidebar options
        st.sidebar.header("Select Date Range:")
        financial_df['month'] = pd.to_datetime(financial_df['month'], errors='coerce')

        start_date = st.sidebar.date_input("Start date", financial_df["month"].min().date())
        end_date = st.sidebar.date_input("End date", financial_df["month"].max().date())

        # Filter data
        filtered_df = financial_df[(financial_df['month'] >= pd.to_datetime(start_date)) & (financial_df['month'] <= pd.to_datetime(end_date))]

        with st.expander("VIEW DATA"):
            showData = st.multiselect('Filter: ',  filtered_df.columns, default=[
                'month','currency','total_sales','total_refunds','total_payouts','net_profit_loss'])
            st.dataframe( filtered_df[showData], use_container_width=True)


        total_sales = filtered_df['total_sales'].sum()
        total_refunds = filtered_df['total_refunds'].sum()
        total_payouts = filtered_df['total_payouts'].sum()
        net_profit_loss = filtered_df['net_profit_loss'].sum()


        total1, total2 = st.columns(2, gap='small')

        with total1:
            st.info('Total Sales',icon="💸")
            st.metric(label="Total Sales", value=f"$ {total_sales:,.0f}")

        with total2:
            st.info('Total Refunds',icon="💸")
            st.metric(label="Total Refunds:", value=f"$ {total_refunds:,.0f}")

        total3, total4 = st.columns(2, gap='small')

        with total3:
            st.info('Total Payouts',icon="💸")
            st.metric(label="Total Payouts:", value=f"$ {total_payouts:,.0f}")

        with total4:
            st.info('Net Pofit & Loss',icon="📊")
            st.metric(label="Net Pofit & Loss:", value=f"$ {net_profit_loss:,.0f}")

        

        # Plotting the data
        st.title("Financial Overview")


        total1, total2 = st.columns(2, gap='small')

        with total1:
            fig_sales = px.bar(filtered_df, x='month', y='total_sales', title='Total Sales Over Time')
            st.plotly_chart(fig_sales)


        with total2:
            fig_refunds = px.bar(filtered_df, x='month', y='total_refunds', title='Total Refunds Over Time')
            st.plotly_chart(fig_refunds)

        total3, total4 = st.columns(2, gap='medium')

        with total3:
            fig_payouts = px.bar(filtered_df, x='month', y='total_payouts', title='Total Payouts Over Time')
            st.plotly_chart(fig_payouts)

        with total4:
            fig_net_profit_loss = px.bar(filtered_df, x='month', y='net_profit_loss', title='Net Profit/Loss Over Time')
            st.plotly_chart(fig_net_profit_loss)
# Main function to handle sidebar navigation
def main():
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket='stripe-raw-data-dashboard', Key='Untitled_report.csv')# Fetch the object from S3
    content = response['Body'].read().decode('utf-8')# Read the content
    dashboard = Dashboard(data=content)

    with st.sidebar:
        selected = option_menu(
            menu_title="Select a Page",
            options=["Revenue", "Customers", "Subscriptions", "Payment", "Financial"],
            icons=["cash", "people", "bar-chart", "credit-card", "file-text"],
            menu_icon="cast",
            default_index=0
        )

    # with st.sidebar:
    #     selected = st.selectbox("Select a Page", ["Revenue", "Customers", "Subscriptions", "Payment", "Financial"])
        
        

    if selected == "Revenue":
        st.title(f"{selected}")
        dashboard.revenue()
    elif selected == "Customers":
        st.header(f"{selected}")
        dashboard.Customers()
    elif selected == "Subscriptions":
        st.header(f"{selected}")
        dashboard.subscriptions()
    elif selected == "Payment":
        st.header(f"{selected}")
        dashboard.payment()
    elif selected == "Financial":
        st.header(f"{selected}")
        dashboard.financial()


if __name__ == "__main__":
    main()