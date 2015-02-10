"""
****************
Core Entrypoints
****************

The ``entrypoints`` package contains all the functions that are called from the 
API. 

The entrypoints call the internal core mechanics found in ``tickee.logic`` and 
manage the database transaction.
""" 

import tickee

import accounts
import crm
import events
import locations
import crm_logging
import tickets
import tickettypes
import users
import security
import orders
