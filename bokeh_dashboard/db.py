import sqlalchemy as sa
import os
import pandas as pd

DB_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432')
engine = sa.create_engine(DB_URL)

meta = sa.MetaData(engine)
crimes = sa.Table('crimes', meta, autoload=True)
year_month = sa.func.date_trunc('month', crimes.c.OCCURRED_ON_DATE).label('year_month')


def get_available_months():
    results = sa.select([year_month.distinct()]).order_by(year_month).execute()
    return [r.year_month.date() for r in results]


def get_available_districts():
    results = sa.select([crimes.c.DISTRICT.distinct().label('district')]).execute()
    return [r.district for r in results if r.district is not None]


def add_filter(query, start_date, end_date, districts):
    return (query
            .where(crimes.c.OCCURRED_ON_DATE.between(start_date, end_date))
            .where(crimes.c.DISTRICT.in_(districts)))


def get_offense_data(start_date, end_date, districts):
    query = (sa.select([year_month,
                        sa.func.count().label('num_offenses'),
                        sa.func.sum(crimes.c.SHOOTING).label('num_shootings')])
             .group_by(year_month)
             .order_by(year_month)
             )
    query = add_filter(query, start_date, end_date, districts)
    return pd.read_sql(query, query.bind)


def get_top10_groups(start_date, end_date, districts):
    query = (sa.select([crimes.c.OFFENSE_CODE_GROUP.label('code_group'),
                        sa.func.count().label('counts')])
             .group_by(crimes.c.OFFENSE_CODE_GROUP)
             .order_by(sa.desc(sa.func.count()))
             .limit(10)
             )
    query = add_filter(query, start_date, end_date, districts)
    return pd.read_sql(query, query.bind)


def get_heatmap_data(start_date, end_date, districts):
    query = (sa.select([crimes.c.DAY_OF_WEEK,
                        crimes.c.HOUR,
                        sa.func.count().label('counts')])
             .group_by(crimes.c.DAY_OF_WEEK, crimes.c.HOUR)
             )
    query = add_filter(query, start_date, end_date, districts)
    df = pd.read_sql(query, query.bind)
    df['DAY_OF_WEEK'] = pd.Categorical(df['DAY_OF_WEEK'],
                                       categories=["Monday",
                                                   "Tuesday",
                                                   "Wednesday",
                                                   "Thursday",
                                                   "Friday",
                                                   "Saturday",
                                                   "Sunday"],
                                       ordered=True)
    df['HOUR'] = df['HOUR'].astype(str)
    return df
