import os
import sqlite3
import pandas as pd
import traceback
from datetime import datetime


DATABASE = "nifty100.db"

RAW_PATH = "data/raw"

OUTPUT_PATH = "output/load_audit.csv"



sqlite_tables = {

    "companies.xlsx": "companies",
    "profitandloss.xlsx": "profitandloss",
    "balancesheet.xlsx": "balancesheet",
    "cashflow.xlsx": "cashflow",
    "stock_prices.xlsx": "stock_prices",
    "financial_ratios.xlsx": "financial_ratios",
    "sectors.xlsx": "sectors",
    "analysis.xlsx": "analysis",
    "documents.xlsx": "documents",
    "prosandcons.xlsx": "prosandcons",
    "peer_groups.xlsx": "peer_groups"

}




COLUMN_MAPS = {

    "sectors.xlsx": {
        "company_id": "ticker"
    },
    
    "balancesheet.xlsx": {

        "id": "bs_id",
        "company_id": "ticker",
        # "equity_share_capital": "equity_capital",
        # "reserves": "reserves",
        # "borrowings": "borrowings",
        # "other_liabilities": "other_liabilities"

    },
     
    "cashflow.xlsx": {

        "id": "cf_id",
        "company_id": "ticker",
        "operating_activity": "operating_cashflow",
        "investing_activity": "investing_cashflow",
        "financing_activity": "financing_cashflow"
    
    }
    

}




def clean_columns(df):

    df = df.dropna(axis=1, how="all")


    df.columns = (

        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("&", "and", regex=False)

    )


    return df






def load_excel(file):

    path = os.path.join(
        RAW_PATH,
        file
    )


    if file in [

        "sectors.xlsx",
        "stock_prices.xlsx",
        "financial_ratios.xlsx",
        "peer_groups.xlsx"

    ]:

        df = pd.read_excel(
            path,
            header=0
        )


    else:

        df = pd.read_excel(
            path,
            header=1
        )



    df = clean_columns(df)



    if file in COLUMN_MAPS:

        df = df.rename(
            columns=COLUMN_MAPS[file]
        )


    return df







def insert_data(df, table, conn):

    print("\n======================")
    print(table)
    print(df.columns.tolist())
    print("======================")
    
    schema = pd.read_sql(

        f"PRAGMA table_info({table})",

        conn

    )


    db_columns = list(
        schema["name"]
    )



    # Fix companies ticker

    if table == "companies":


        if "ticker" not in df.columns:


            if "id" in df.columns:

                df["ticker"] = df["id"]


            elif "company_name" in df.columns:

                df["ticker"] = df["company_name"]


            else:

                raise Exception(
                    f"companies missing ticker. Columns: {list(df.columns)}"
                )
                
    # Fix balancesheet mapping
    if table == "balancesheet":

        companies = pd.read_sql(
            "SELECT company_id, ticker FROM companies",
            conn
        )

        ticker_map = dict(
            zip(companies["ticker"], companies["company_id"])
        )

        df["company_id"] = df["ticker"].map(ticker_map)
        
    # Fix cashflow mapping
    if table == "cashflow":

        companies = pd.read_sql(
            "SELECT company_id, ticker FROM companies",
            conn
          )

        ticker_map = dict(
            zip(companies["ticker"], companies["company_id"])
          )
        df["company_id"] = df["ticker"].map(ticker_map) 

        



    # Fix sectors ticker

    if table == "sectors":


        if "company_id" in df.columns:

            df["ticker"] = df["company_id"]




    matching_columns = [

        col for col in df.columns

        if col in db_columns

    ]



    if not matching_columns:


        raise Exception(

            f"No matching columns found: {list(df.columns)}"

        )



    df = df[matching_columns]



    df.to_sql(

        table,

        conn,

        if_exists="append",

        index=False

    )









def main():


    os.makedirs(

        "output",

        exist_ok=True

    )


    conn = sqlite3.connect(
        DATABASE
    )


    audit = []




    for file, table in sqlite_tables.items():


        try:


            df = load_excel(file)



            insert_data(

                df,

                table,

                conn

            )



            print(

                table,

                "loaded",

                len(df)

            )



            audit.append({

                "table": table,

                "rows": len(df),

                "status": "SUCCESS",

                "time": datetime.now()

            })




        except Exception as e:

             print(f"\n===== {table} FAILED =====")
             traceback.print_exc()



             audit.append({

                "table": table,

                "rows": 0,

                "status": str(e),

                "time": datetime.now()

            })






    conn.commit()



    pd.DataFrame(audit).to_csv(

        OUTPUT_PATH,

        index=False

    )



    conn.close()



    print(

        "ETL Load Completed!"

    )







if __name__ == "__main__":

    main()