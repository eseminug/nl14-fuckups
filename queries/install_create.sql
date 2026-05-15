select
    datetime,
    payment_account_id
from
    default.ug_rt_unified_identification_events
where
    date >= toDate('{last_date}')
and
    event = 'install_create'
and
    payment_account_id > 0
