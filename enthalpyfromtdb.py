import pandas as pd
import xarray as xr
from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import streamlit as st
import tempfile

# Create a Streamlit app
st.title("Equilibrium Calculation and Enthalpy Visualization")

# Upload a .tdb file
uploaded_file = st.file_uploader("Upload a .tdb file", type=["tdb"])

if uploaded_file is not None:
    # Save the uploaded BytesIO object to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tdb_file:
        tdb_file.write(uploaded_file.read())
        tdb_path = tdb_file.name

    # Process the uploaded .tdb file
    dbf = Database(tdb_path)

    # Input field for selecting elements via a dropdown
    st.sidebar.header("Select Elements")
    default_elements = list(dbf.elements)  # Use the elements from the database
    selected_elements = st.multiselect("Select Elements", sorted(default_elements), default=default_elements)

    # Remove the element that is alphabetically the farthest by default
    farthest_element = max(selected_elements)
    selected_elements.remove(farthest_element)

    # Input fields for equilibrium conditions
    st.sidebar.header("Equilibrium Conditions")
    user_temperature_start = st.sidebar.number_input("Starting Temperature (K)", 300, 2000, 300)
    user_temperature_end = st.sidebar.number_input("Ending Temperature (K)", user_temperature_start, 1850, 1850)
    user_temperature_step = st.sidebar.number_input("Temperature Step (K)", 1, 100, 10)
    user_pressure = st.sidebar.number_input("Pressure (Pa)", 101325)

    # Input fields for mole fractions (excluding 'VA')
    user_mole_fractions = {}
    for element in selected_elements:
        if element != 'VA':
            user_mole_fractions[element] = st.sidebar.number_input(f"Mole Fraction of {element}", 0.0, 1.0, 0.1)

    # Include the element excluded from mole fractions in selected_elements
    selected_elements.append(farthest_element)

    # Perform the equilibrium calculation with user-defined conditions
    user_conditions = {v.T: (user_temperature_start, user_temperature_end, user_temperature_step), v.P: user_pressure}
    for element, fraction in user_mole_fractions.items():
        if element != farthest_element:
            user_conditions[v.X(element)] = fraction

    # Equilibrium calculation with selected_elements (including 'VA') and user_conditions
    eq_result = equilibrium(dbf, selected_elements, ['LIQUID', 'HCP_A3'], user_conditions, output='HM')

    # Extract values from the DataArray and then flatten
    T_values = eq_result.T.values.flatten()
    HM_values = eq_result.HM.values.flatten()

    # Create a DataFrame from the flattened data
    result_df = pd.DataFrame({'T': T_values, 'H': HM_values})

    # Display a download link for the CSV file
    csv_file_path = 'equilibrium_results.csv'
    st.markdown("### Download CSV Results")
    st.markdown("Click below to download the CSV results:")
    st.download_button(
        label="Download CSV",
        data=result_df.to_csv(index=False).encode(),
        key="download-csv",  # Unique key
        on_click=None,
        args=(csv_file_path,),
        file_name="equilibrium_results.csv",
    )

    # Create a line chart for H and T
    st.markdown("### Enthalpy vs. Temperature Chart")
    st.line_chart(result_df.set_index('T')[['H']])

    # Plot the Enthalpy vs. Temperature
    st.pyplot(plt.figure(figsize=(8, 6)))

