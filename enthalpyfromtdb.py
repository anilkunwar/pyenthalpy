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

equilibrium_results = []  # List to store equilibrium results

if uploaded_file is not None:
    # Save the uploaded BytesIO object to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tdb_file:
        tdb_file.write(uploaded_file.read())
        tdb_path = tdb_file.name

    # Process the uploaded .tdb file
    dbf = Database(tdb_path)

    condition_counter = 0  # Unique identifier for condition sets

    while True:
        condition_counter += 1  # Increment the condition set counter

        # Input field for selecting elements via a dropdown
        st.sidebar.header("Select All the Elements of the Alloy and Exclude VA here. It will be included later on.")
        default_elements = list(dbf.elements)  # Use the elements from the database
        selected_elements = st.multiselect(
            f"Select Elements (Set {condition_counter})",  # Add a unique identifier
            sorted(default_elements),
            default=default_elements
        )

        # Remove the element that is alphabetically the farthest by default
        # For N element alloy, the composition information of N-1 element will be sufficient
        # This part will remove the information of the farthest element (in alphabetical order)
        farthest_element = max(selected_elements)
        selected_elements.remove(farthest_element)

        # Input fields for equilibrium conditions
        st.sidebar.header("Equilibrium Conditions")
        user_temperature_start = st.sidebar.number_input(
            f"Starting Temperature (K) (Set {condition_counter})", 300, 2000, 300
        )
        user_temperature_end = st.sidebar.number_input(
            f"Ending Temperature (K) (Set {condition_counter})", 305, 3000, 1850
        )
        user_temperature_step = st.sidebar.number_input(
            f"Temperature Step (K) (Set {condition_counter})", 1, 200, 10
        )
        user_pressure = st.sidebar.number_input(
            f"Pressure (Pa) (Set {condition_counter})", 101325
        )

        # Input fields for mole fractions (excluding 'VA')
        user_mole_fractions = {}
        for element in selected_elements:
            if element != 'VA':
                user_mole_fractions[element] = st.sidebar.number_input(
                    f"Mole Fraction of {element} (Set {condition_counter})", 0.0, 1.0, 0.1
                )

        # The composition information in eq_result i.e. selected_elements will have to include all of the elements + VA
        # Include the element excluded from mole fractions in selected_elements
        selected_elements.append(farthest_element)
        # Append 'VA' to the selected_elements for eq_result
        selected_elements.append('VA')

        # Perform the equilibrium calculation with user-defined conditions
        user_conditions = {v.T: (user_temperature_start, user_temperature_end, user_temperature_step), v.P: user_pressure}
        for element, fraction in user_mole_fractions.items():
            if element != farthest_element:
                user_conditions[v.X(element)] = fraction

        # Equilibrium calculation with selected_elements (including 'VA') and user_conditions
        #eq_result = equilibrium(dbf, selected_elements, ['LIQUID', 'HCP_A3'], user_conditions, output='HM')
        # To allow the selection of any two phases from the list of available phases in the TDB (or tdb) file
        # Define a function to select two phases from the available phases
        #def select_phases(phases):
            #print("Available phases:", phases)
            #phase1 = input("Enter the first phase: ").strip()
            #phase2 = input("Enter the second phase: ").strip()
            #return [phase1, phase2]

        ## Get the user-selected phases
        #selected_phases = select_phases(dbf.phases.keys())
         # Fetch available phases from the database
        available_phases = list(dbf.phases.keys())

        # Multiselect box for selecting equilibrium phases
        #selected_phases = st.sidebar.multiselect(
        #    f"Select Equilibrium Phases (Set {condition_counter})",
        #    available_phases,
        #    default=['LIQUID', 'HCP_A3']
        #)
        # Get the first two phases listed in the database as default phases
        default_phases = available_phases[:2]

        # Multiselect box for selecting equilibrium phases
        selected_phases = st.sidebar.multiselect(
            f"Select Equilibrium Phases (Set {condition_counter})",
            available_phases,
            default=default_phases
        )

        # Run equilibrium calculation with user-selected phases
        eq_result = equilibrium(dbf, selected_elements, selected_phases, user_conditions, output='HM')

        # Extract values from the DataArray and then flatten
        T_values = eq_result.T.values.flatten()
        HM_values = eq_result.HM.values.flatten()

        # Create a DataFrame from the flattened data
        #result_df = pd.DataFrame({'T': T_values, 'H': HM_values})
        # Create a DataFrame from the flattened data
        result_df = pd.DataFrame({'S.N.': range(1, len(T_values) + 1), 'T': T_values, 'H': HM_values})

        equilibrium_results.append(result_df)  # Append the result for this set of input values

        # Create a unique key for the checkbox based on the condition set
        add_more = st.sidebar.checkbox(
            f"Add More Equilibrium Conditions? (Set {condition_counter + 1})",  # Add a unique identifier
            key=f"add_more_{condition_counter}",
        )

        if not add_more:
            break

    # Concatenate all equilibrium results into a single DataFrame
    combined_results_df = pd.concat(equilibrium_results, ignore_index=True)

    # Display a download link for the CSV file
    csv_file_path = 'equilibrium_results.csv'
    st.markdown("### Download CSV Results")
    st.markdown("Click below to download the CSV results:")
    st.download_button(
        label="Download CSV",
        data=combined_results_df.to_csv(index=False).encode(),
        key="download-csv",  # Unique key
        on_click=None,
        args=(csv_file_path,),
        file_name="equilibrium_results.csv",
    )

    # Create a line chart for H and T
    st.markdown("### Enthalpy vs. Temperature Chart")
    st.line_chart(combined_results_df.set_index('T')[['H']])



    # Plot the Enthalpy vs. Temperature
    st.pyplot(plt.figure(figsize=(8, 6)))

