import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import os
from manufacturing_calculator import calculate_price, calculate_machine_cost_per_hour, calculate_multi_quantity_prices
from utils import (
    validate_inputs, 
    get_download_link, 
    save_preset, 
    load_preset, 
    get_all_presets, 
    delete_preset
)

# Set page configuration
st.set_page_config(
    page_title="Manufacturing Cost Calculator",
    page_icon="🏭",
    layout="centered"
)

# App title and description
st.title("Kalkulator proizvodnih stroškov in cen izdelkov")
st.markdown("""

Ta kalkulator vam pomaga določiti ceno na kos za proizvedene izdelke
na podlagi stroškov stroja, materialov in proizvodnega časa.
""")

# Create an expander for Machine Cost Calculator
with st.expander("Kalkulator cene stroja na uro", expanded=False):
    st.markdown("""
Tukaj se preračuna strojna ura cevnega laserja katera se samodejno prikaže v polju strojna ura pri izračunu cene izdelka.
    """)
    
    # Create a form for machine cost inputs
    with st.form("machine_cost_form"):
        st.subheader("Vnesite parametre stroškov stroja")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Electricity costs
            electricity_cost_per_hour = st.number_input(
                " Strošek elektrike na uro (€)",
                min_value=0.0,
                value=0.0,
                help="Strošek elektrike, ki jo porabi stroj na uro"
            )
            
            # Maintenance costs
            maintenance_cost_per_hour = st.number_input(
                "Strošek vzdrževanja na uro (€)",
                min_value=0.0,
                value=0.0,
                help="Strošek vzdrževanja stroja na uro"
            )
            
            # Depreciation costs
            depreciation_cost_per_hour = st.number_input(
                "Strošek amortizacije na uro (€)",
                min_value=0.0, 
                value=0.0,
                help="Strošek amortizacije stroja na uro"
            )
        
        with col2:
            # Facility costs
            facility_cost_per_hour = st.number_input(
                "Strošek objekta na uro (€)",
                min_value=0.0,
                value=0.0,
                help="Strošek objekta/prostora, ki ga uporablja stroj na uro"
            )
            
            # Labor costs - added this field
            labor_cost_per_hour = st.number_input(
                "Strošek operaterja na uro (€)",
                min_value=0.0,
                value=0.0,
                help="Strošek dela na uro"
            )
            
            # Other costs
            other_costs_per_hour = st.number_input(
                "Ostali  stroški na uro (€)",
                min_value=0.0,
                value=0.0,
                help="Morebitni drugi stroški, povezani s strojem na uro"
            )
        
        # Calculate button
        calculate_machine_cost_button = st.form_submit_button("Izračunaj strojno uro")
    
    # Calculate and display machine cost when form is submitted
    if calculate_machine_cost_button:
        # Calculate machine cost per hour
        calculated_machine_cost = calculate_machine_cost_per_hour(
            electricity_cost_per_hour,
            maintenance_cost_per_hour,
            depreciation_cost_per_hour,
            facility_cost_per_hour,
            other_costs_per_hour,
            labor_cost_per_hour
        )
        
        # Display the result
        st.success(f"Strojna ura: ${calculated_machine_cost:.2f}")
        
        # Store the value in session state for use in the main form
        st.session_state['machine_cost_per_hour'] = calculated_machine_cost
        
        # Store the machine cost details for the report
        st.session_state['machine_cost_details'] = {
            'electricity': electricity_cost_per_hour,
            'maintenance': maintenance_cost_per_hour,
            'depreciation': depreciation_cost_per_hour,
            'facility': facility_cost_per_hour,
            'labor': labor_cost_per_hour,
            'other': other_costs_per_hour,
            'total': calculated_machine_cost
        }
        
        # Create a breakdown of machine costs
        machine_cost_data = {
            "Stroškovna komponenta": [
                "Elektrika",
                "Vzdrževanje",
                "Amortizacija",
                "Objekt",
                "Delo",
                "Drugi stroški",
                "Skupni strošek stroja"
            ],
            "Znesek na uro (€)": [
                f"{electricity_cost_per_hour:.2f}",
                f"{maintenance_cost_per_hour:.2f}",
                f"{depreciation_cost_per_hour:.2f}",
                f"{facility_cost_per_hour:.2f}",
                f"{labor_cost_per_hour:.2f}",
                f"{other_costs_per_hour:.2f}",
                f"{calculated_machine_cost:.2f}"
            ]
        }
        
        machine_cost_df = pd.DataFrame(machine_cost_data)
        st.table(machine_cost_df)

# Initialize session state for machine cost if not exists
if 'machine_cost_per_hour' not in st.session_state:
    st.session_state['machine_cost_per_hour'] = 0.0

# Handle preset loading if specified in URL parameters
query_params = st.query_params
if 'preset' in query_params:
    preset_name = query_params['preset']
    preset_data = load_preset(preset_name)
    
    if preset_data:
        # Update session state with preset data
        for key, value in preset_data.items():
            if key == 'machine_cost_details':
                st.session_state['machine_cost_details'] = value
            else:
                st.session_state[key] = value
        
        st.success(f"Preset '{preset_name}' loaded automatically. / Prednastavitev '{preset_name}' samodejno naložena.")

# Create a form for user inputs
with st.form("manufacturing_form"):
    st.subheader("Vnesite proizvodne parametre")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Machine costs (using the calculated value if available)
        machine_cost_per_hour = st.number_input(
            "Strojna ura (€)",
            min_value=0.0,
            value=st.session_state['machine_cost_per_hour'],
            help="Strošek delovanja stroja na uro, vključno z delom, elektriko, vzdrževanjem itd."
        )
        
        # Material costs
        material_cost_per_unit = st.number_input(
            "Strošek materiala na enoto (€)",
            min_value=0.0,
            value=st.session_state.get('material_cost_per_unit', 0.0),
            help="Strošek surovega materiala, uporabljenega za en kos"
        )
        
        # Additional material costs
        additional_material_cost = st.number_input(
            "Dodatni stroški materiala (€)",
            min_value=0.0,
            value=st.session_state.get('additional_material_cost', 0.0),
            help="Dodatni stroški materiala na kos"
        )
    
    with col2:
        # Production time
        production_time_minutes = st.number_input(
            "Proizvodni čas (minut na kos)",
            min_value=0.0,
            value=st.session_state.get('production_time_minutes', 0.0),
            help="Čas, potreben za izdelavo enega kosa"
        )
        
        # Note: The original labor cost field is removed as it's included in machine cost
        
        # Empty space to maintain column alignment
        st.markdown("Opomba: Strošek dela je že vključen v strošek stroja na uro.")
        
        
        # Overhead percentage
        overhead_percentage = st.number_input(
            "Odstotek režije (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.get('overhead_percentage', 20.0),
            help="Odstotek za režijske stroške"
        )
    
    # Profit margin
    profit_margin_percentage = st.slider(
        "Profitna marža (%)",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get('profit_margin_percentage', 25.0),
        help="Želeni odstotek profitne marže"
    )
    
    # Batch size for calculation
    batch_size = st.number_input(
        "Batch Size (number of pieces) / Velikost serije (število kosov)",
        min_value=1,
        value=st.session_state.get('batch_size', 1),
        help="Število kosov v proizvodnji seriji"
    )
    
    # Submit button
    submit_button = st.form_submit_button("Izračunaj ceno")

# Calculate and display results when form is submitted
if submit_button:
    # Labor cost is included in machine cost, so we don't need a separate variable
    
    # Store parameters in session state for multi-quantity calculator to use
    st.session_state['submitted_params'] = {
        'machine_cost_per_hour': machine_cost_per_hour,
        'material_cost_per_unit': material_cost_per_unit,
        'production_time_minutes': production_time_minutes,
        'overhead_percentage': overhead_percentage,
        'profit_margin_percentage': profit_margin_percentage,
        'additional_material_cost': additional_material_cost,
        'batch_size': batch_size
    }
    
    # Validate inputs
    validation_result, message = validate_inputs(
        machine_cost_per_hour,
        material_cost_per_unit,
        production_time_minutes,
        0.0,  # labor_cost_per_hour set to 0
        overhead_percentage,
        profit_margin_percentage,
        batch_size
    )
    
    if not validation_result:
        st.error(message)
    else:
        # Perform calculations - set include_labor_cost to False since it's included in machine cost
        results = calculate_price(
            machine_cost_per_hour,
            material_cost_per_unit,
            production_time_minutes,
            0.0,  # labor_cost_per_hour set to 0
            overhead_percentage,
            profit_margin_percentage,
            additional_material_cost,
            batch_size,
            include_labor_cost=False  # Tell the function not to include labor cost separately
        )
        
        # Display results
        st.subheader("Rezultati")
        
        # Main result boxes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Cena na kos (€)", value=f"{results['price_per_piece']:.2f}")
        with col2:
            st.metric(label="Skupni strošek serije (€)", value=f"{results['total_batch_cost']:.2f}")
        with col3:
            st.metric(label="Dobiček na kos (€)", value=f"{results['profit_per_piece']:.2f}")
        
        # Detailed breakdown
        st.subheader("Cost Breakdown / Razčlenitev stroškov")
        
        # Create a DataFrame for the cost breakdown
        breakdown_data = {
            "Stroškovna komponenta": [
                "Strošek stroja (vključno z delom)",
                "Strošek materiala",
                "Dodatni strošek materiala",
                "Režijski stroški",
                "Osnovni strošek (pred dobičkom)",
                "Dobiček",
                "Skupna cena na kos"
            ],
            "Znesek (€)": [
                f"{results['machine_cost_per_piece']:.2f}",
                f"{results['material_cost_per_piece']:.2f}",
                f"{results['additional_material_cost']:.2f}",
                f"{results['overhead_cost_per_piece']:.2f}",
                f"{results['base_cost_per_piece']:.2f}",
                f"{results['profit_per_piece']:.2f}",
                f"{results['price_per_piece']:.2f}"
            ],
            "Odstotek (%)": [
                f"{results['machine_cost_percentage']:.2f}%",
                f"{results['material_cost_percentage']:.2f}%",
                f"{results['additional_material_cost_percentage']:.2f}%",
                f"{results['overhead_cost_percentage']:.2f}%",
                f"{results['base_cost_percentage']:.2f}%",
                f"{results['profit_percentage']:.2f}%",
                "100.00%"
            ]
        }
        
        breakdown_df = pd.DataFrame(breakdown_data)
        st.table(breakdown_df)
        
        # Add pie chart for visualization
        st.subheader("Stroškovna porazdelitev")
        
        # Create pie chart data
        pie_labels = [
            "Strošek stroja (vključno z delom)", 
            "Strošek materiala", 
            "Dodatni strošek materiala", 
            "Režijski stroški", 
            "Dobiček"
        ]
        
        pie_values = [
            results['machine_cost_per_piece'],
            results['material_cost_per_piece'],
            results['additional_material_cost'],
            results['overhead_cost_per_piece'],
            results['profit_per_piece']
        ]
        
        # Generate the chart
        fig = {
            'data': [{
                'values': pie_values,
                'labels': pie_labels,
                'type': 'pie',
                'hole': 0.4,
                'hoverinfo': 'label+percent+value',
                'textinfo': 'percent'
            }],
            'layout': {
                'showlegend': True,
                'margin': {'t': 5, 'l': 5, 'r': 5, 'b': 5},
                'height': 400
            }
        }
        
        st.plotly_chart(fig)
        
        # Export options
        st.subheader("Izvoz rezultatov")
        
        # Create a CSV file for download
        csv_data = io.StringIO()
        breakdown_df.to_csv(csv_data, index=False)
        
        # Create a text summary
        machine_cost_breakdown = ""
        if 'machine_cost_details' in st.session_state:
            details = st.session_state['machine_cost_details']
            machine_cost_breakdown = f"""
        Machine Cost Breakdown (per Hour) / Razčlenitev stroškov stroja (na uro):
        - Electricity / Elektrika: ${details['electricity']:.2f}
        - Maintenance / Vzdrževanje: ${details['maintenance']:.2f}
        - Depreciation / Amortizacija: ${details['depreciation']:.2f}
        - Facility / Objekt: ${details['facility']:.2f}
        - Labor / Delo: ${details['labor']:.2f}
        - Other Costs / Drugi stroški: ${details['other']:.2f}
        - Total Machine Cost / Skupni strošek stroja: ${details['total']:.2f}
        """
        
        calculation_summary = f"""
        Manufacturing Cost Calculator Results / Rezultati kalkulatorja proizvodnih stroškov
        =================================================================================
        
        Input Parameters / Vhodni parametri:
        - Machine Cost per Hour / Strošek stroja na uro: ${machine_cost_per_hour:.2f}
        - Material Cost per Unit / Strošek materiala na enoto: ${material_cost_per_unit:.2f}
        - Additional Material Cost / Dodatni stroški materiala: ${additional_material_cost:.2f}
        - Production Time / Proizvodni čas: {production_time_minutes:.2f} minutes per piece / minut na kos
        - Overhead Percentage / Odstotek režije: {overhead_percentage:.2f}%
        - Profit Margin / Profitna marža: {profit_margin_percentage:.2f}%
        - Batch Size / Velikost serije: {batch_size} pieces / kosov
        {machine_cost_breakdown}
        Calculation Results / Rezultati izračuna:
        - Price per Piece / Cena na kos: ${results['price_per_piece']:.2f}
        - Total Batch Cost / Skupni strošek serije: ${results['total_batch_cost']:.2f}
        - Profit per Piece / Dobiček na kos: ${results['profit_per_piece']:.2f}
        
        Cost Breakdown per Piece / Razčlenitev stroškov na kos:
        - Machine Cost (including labor) / Strošek stroja (vključno z delom): ${results['machine_cost_per_piece']:.2f} ({results['machine_cost_percentage']:.2f}%)
        - Material Cost / Strošek materiala: ${results['material_cost_per_piece']:.2f} ({results['material_cost_percentage']:.2f}%)
        - Additional Material Cost / Dodatni strošek materiala: ${results['additional_material_cost']:.2f} ({results['additional_material_cost_percentage']:.2f}%)
        - Overhead Cost / Režijski stroški: ${results['overhead_cost_per_piece']:.2f} ({results['overhead_cost_percentage']:.2f}%)
        - Base Cost / Osnovni strošek: ${results['base_cost_per_piece']:.2f} ({results['base_cost_percentage']:.2f}%)
        - Profit / Dobiček: ${results['profit_per_piece']:.2f} ({results['profit_percentage']:.2f}%)
        """
        
        # Create columns for the download buttons
        col1, col2 = st.columns(2)
        with col1:
            # CSV download
            csv_download_link = get_download_link(
                csv_data.getvalue(),
                "manufacturing_cost_calculation.csv",
                "PRENESI CSV"
            )
            st.markdown(csv_download_link, unsafe_allow_html=True)
        
        with col2:
            # Text download
            txt_download_link = get_download_link(
                calculation_summary,
                "manufacturing_cost_calculation.txt",
                "PRENESI TXT"
            )
            st.markdown(txt_download_link, unsafe_allow_html=True)
        
        # Save calculation as preset option
        st.subheader("Shrani izračun kot prednastavitev")
        
        # Input field for preset name
        preset_name = st.text_input("Ime prednastavitve", 
                                   placeholder="Vnesite ime za to prednastavitev")
        
        # Button to save preset
        save_preset_button = st.button("Shrani prednastavitev")
        
        if save_preset_button and preset_name:
            # Create data to save
            preset_data = {
                'machine_cost_per_hour': machine_cost_per_hour,
                'material_cost_per_unit': material_cost_per_unit,
                'production_time_minutes': production_time_minutes,
                'overhead_percentage': overhead_percentage,
                'profit_margin_percentage': profit_margin_percentage,
                'additional_material_cost': additional_material_cost,
                'batch_size': batch_size
            }
            
            # Add machine cost details if available
            if 'machine_cost_details' in st.session_state:
                preset_data['machine_cost_details'] = st.session_state['machine_cost_details']
            
            # Save the preset
            if save_preset(preset_name, preset_data):
                st.success(f"Prednastavitev '{preset_name}' uspešno shranjena!")
            else:
                st.error("Napaka pri shranjevanju prednastavitve.")

# Presets management section
st.subheader("Upravljanje prednastavitev")
st.markdown("""
Naložite, uporabite ali izbrišite shranjene prednastavitve izračunov. To vam omogoča hitro preklapljanje med različnimi scenariji izračuna.
""")

with st.expander("Upravljanje prednastavitev", expanded=True):
    # Get all available presets
    available_presets = get_all_presets()
    
    if not available_presets:
        st.info("Ni najdenih prednastavitev. Ustvarite izračun in ga shranite kot prednastavitev.")
    else:
        # Display available presets in a selectbox
        selected_preset = st.selectbox(
            "Izberite prednastavitev",
            available_presets
        )
        
        # Create columns for buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Button to load preset
            load_preset_button = st.button("Naloži prednastavitev")
        
        with col2:
            # Button to delete preset
            delete_preset_button = st.button("Izbriši prednastavitev")
        
        # Handle loading preset
        if load_preset_button and selected_preset:
            preset_data = load_preset(selected_preset)
            
            if preset_data:
                # Update session state with preset data
                for key, value in preset_data.items():
                    if key == 'machine_cost_details':
                        st.session_state['machine_cost_details'] = value
                    else:
                        st.session_state[key] = value
                
                st.success(f"Prednastavitev '{selected_preset}' naložena! Osvežite stran, da vidite naložene vrednosti v kalkulatorju.")
                st.button("Osveži stran", on_click=lambda: st.rerun())
            else:
                st.error(f"Napaka pri nalaganju prednastavitve '{selected_preset}'.")
        
        # Handle deleting preset
        if delete_preset_button and selected_preset:
            confirm_delete = st.checkbox("Potrdi izbris")
            
            if confirm_delete:
                if delete_preset(selected_preset):
                    st.success(f"Preset '{selected_preset}' deleted. / Prednastavitev '{selected_preset}' izbrisana.")
                    st.button("Osveži", on_click=lambda: st.rerun())
                else:
                    st.error(f"Napaka pri brisanju prednastavitve '{selected_preset}'.")

# Multi-quantity pricing calculator
st.subheader("Kalkulator cen za več količin")
st.markdown("""
Izračunajte cene za več različnih količin z upoštevanjem nastavitvenih časov.
To pomaga določiti prelomne točke cen za različne količine naročila.
""")

with st.expander("Določanje cen za več količin", expanded=True):
    # Create a form for multi-quantity pricing inputs
    with st.form("multi_quantity_form"):
        st.subheader("Vnesite parametre za več količin")
        
        # Setup time
        setup_time_minutes = st.number_input(
            "Čas nastavitve (minut)",
            min_value=0.0,
            value=30.0,
            help="Čas, potreben za nastavitev stroja pred proizvodnjo. Ta strošek se porazdeli med vse kose v seriji."
        )
        
        # Separate setup cost rate option
        different_setup_cost = st.checkbox(
            "Uporabi drugačno cenovno stopnjo za čas nastavitve?", 
            value=False,
            help="Omogočite, če je strošek na uro med nastavitvijo drugačen od redne proizvodnje"
        )
        
        setup_cost_per_hour = None
        if different_setup_cost:
            # Get machine cost from session state if available
            default_value = 0.0
            if 'submitted_params' in st.session_state:
                default_value = st.session_state['submitted_params'].get('machine_cost_per_hour', 0.0)
                
            setup_cost_per_hour = st.number_input(
                "Strošek nastavitve na uro (€)",
                min_value=0.0,
                value=default_value,
                help="Strošek na uro med časom nastavitve (običajno enak strošku stroja na uro)"
            )
        
        # Material discount tiers
        enable_material_discounts = st.checkbox(
            "Omogoči popuste na količino materiala?", 
            value=True,
            help="Uporabi popuste na stroške materiala za večje količine"
        )
        
        material_discount_tiers = {}
        if enable_material_discounts:
            col1, col2 = st.columns(2)
            
            with col1:
                qty1 = st.number_input("Količinski razred 1", min_value=2, value=10)
                qty2 = st.number_input("Količinski razred 2", min_value=2, value=50) 
                qty3 = st.number_input("Količinski razred 3", min_value=2, value=100)
            
            with col2:
                disc1 = st.number_input("Popust % za razred 1", min_value=0.0, max_value=100.0, value=5.0)
                disc2 = st.number_input("Popust % za razred 2", min_value=0.0, max_value=100.0, value=10.0)
                disc3 = st.number_input("Popust % za razred 3", min_value=0.0, max_value=100.0, value=15.0)
            
            material_discount_tiers = {qty1: disc1, qty2: disc2, qty3: disc3}
        
        # Quantity options
        st.subheader("Vnesite količine za izračun")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            qty_1 = st.number_input("Količina 1", min_value=1, value=1)
            qty_2 = st.number_input("Količina 2", min_value=1, value=2)
        
        with col2:
            qty_3 = st.number_input("Količina 3", min_value=1, value=5)
            qty_4 = st.number_input("Količina 4", min_value=1, value=10)
        
        with col3:
            qty_5 = st.number_input("Količina 5", min_value=1, value=20)
            qty_6 = st.number_input("Količina 6", min_value=1, value=50)
            
        # Submit button
        multi_qty_submit_button = st.form_submit_button("Izračunaj cene za več količin")
    
    # Calculate and display multi-quantity results when form is submitted
    if multi_qty_submit_button:
        # Check if parameters have been submitted from the main form
        if 'submitted_params' not in st.session_state:
            st.error("Please fill out and submit the main Manufacturing Parameters form first.")
        else:
            # Get parameters from session state
            params = st.session_state['submitted_params']
            machine_cost_per_hour = params.get('machine_cost_per_hour', 0)
            material_cost_per_unit = params.get('material_cost_per_unit', 0)
            production_time_minutes = params.get('production_time_minutes', 0)
            overhead_percentage = params.get('overhead_percentage', 20.0)
            profit_margin_percentage = params.get('profit_margin_percentage', 25.0)
            additional_material_cost = params.get('additional_material_cost', 0)
            
            # Check for missing required parameters
            missing = []
            if machine_cost_per_hour == 0:
                missing.append("Machine Cost per Hour")
            if material_cost_per_unit == 0:
                missing.append("Material Cost per Unit")
            if production_time_minutes == 0:
                missing.append("Production Time")
                
            if missing:
                st.error(f"Missing required parameters: {', '.join(missing)}. Please complete the main form first.")
            else:
                # Collect all quantities in a list
                quantities = [qty_1, qty_2, qty_3, qty_4, qty_5, qty_6]
                
                # Remove any duplicates and sort
                quantities = sorted(list(set(quantities)))
                
                # Validate inputs
                validation_result, message = validate_inputs(
                    machine_cost_per_hour,
                    material_cost_per_unit,
                    production_time_minutes,
                    0.0,  # labor_cost_per_hour set to 0
                    overhead_percentage,
                    profit_margin_percentage,
                    max(quantities)  # Use the largest quantity for validation
                )
                
                if not validation_result:
                    st.error(message)
                else:
                    # Calculate multi-quantity pricing
                    multi_qty_results = calculate_multi_quantity_prices(
                        machine_cost_per_hour,
                        material_cost_per_unit,
                        production_time_minutes,
                        setup_time_minutes,
                        quantities,
                        setup_cost_per_hour,
                        material_discount_tiers,
                        overhead_percentage,
                        profit_margin_percentage,
                        additional_material_cost,
                        include_labor_cost=False,  # Labor cost is included in machine cost
                        labor_cost_per_hour=0.0
                    )
                    
                    # Display results in a table
                    st.subheader("Multi-Quantity Pricing Results / Rezultati cen za več količin")
                    
                    # Create a DataFrame for the multi-quantity results in both languages
                    qty_data = []
                    for qty, result in multi_qty_results.items():
                        qty_data.append({
                            "Quantity / Kolicina": qty,
                            "Cena na kos (€)": f"{result['price_per_piece']:.2f}",
                            "Skupni strosek (€)": f"{result['total_cost']:.2f}",
                            "Strosek nastavitve na kos (€)": f"{result['setup_cost_per_piece']:.2f}",
                            "Popust na material (%)": f"{result['material_discount_percentage']:.1f}%",
                            "Znizan strosek materiala ($)": f"{result['discounted_material_cost']:.2f}"
                        })
                    
                    multi_qty_df = pd.DataFrame(qty_data)
                    st.table(multi_qty_df)
                    
                    # Create a chart to visualize price breaks
                    qty_values = [int(q) for q in multi_qty_results.keys()]
                    price_values = [float(result['price_per_piece']) for result in multi_qty_results.values()]
                    
                    price_chart = {
                        'data': [{
                            'x': qty_values,
                            'y': price_values,
                            'type': 'scatter',
                            'mode': 'lines+markers',
                            'marker': {'size': 10},
                            'line': {'width': 3},
                            'name': 'Price per Piece / Cena na kos'
                        }],
                        'layout': {
                            'title': 'Prelomne tocke cen po kolicini',
                            'xaxis': {'title': 'Kolicina', 'type': 'log', 'tickvals': qty_values},
                            'yaxis': {'title': 'Cena na kos (€)'},
                            'margin': {'t': 40, 'l': 60, 'r': 40, 'b': 60},
                            'height': 400
                        }
                    }
                    
                    st.plotly_chart(price_chart)
                    
                    # Add a download option for multi-quantity results
                    st.subheader("Izvozi rezultate za več količin")
                    
                    csv_multi_qty = io.StringIO()
                    multi_qty_df.to_csv(csv_multi_qty, index=False)
                    
                    multi_qty_csv_link = get_download_link(
                        csv_multi_qty.getvalue(),
                        "multi_quantity_pricing.csv",
                        "Prenesi rezultate za več količin kot CSV"
                    )
                    st.markdown(multi_qty_csv_link, unsafe_allow_html=True)
                    
                    # Generate summary text of multi-quantity pricing in both languages
                    multi_qty_summary = "Rezultati cen za več količin:\n\n"
                    for qty, result in multi_qty_results.items():
                        multi_qty_summary += f"Količina: {qty}\n"
                        multi_qty_summary += f"- Cena na kos: ${result['price_per_piece']:.2f}\n"
                        multi_qty_summary += f"- Skupni strošek: ${result['total_cost']:.2f}\n"
                        multi_qty_summary += f"- Strošek nastavitve na kos: ${result['setup_cost_per_piece']:.2f}\n"
                        multi_qty_summary += f"- Popust na material: {result['material_discount_percentage']:.1f}%\n"
                        multi_qty_summary += f"- Znižan strošek materiala: ${result['discounted_material_cost']:.2f}\n\n"
                    
                    multi_qty_txt_link = get_download_link(
                        multi_qty_summary,
                        "multi_quantity_pricing.txt",
                        "Prenesi rezultate za več količin kot TXT"
                    )
                    st.markdown(multi_qty_txt_link, unsafe_allow_html=True)
