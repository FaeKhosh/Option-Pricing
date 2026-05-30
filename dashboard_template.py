import os
import shutil
import re
import subprocess
import json
import time
import zipfile
import io
import base64
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from threading import Thread

import base64
import dash
from dash import dcc, html, Input, Output, State, callback, ALL, dash_table
import plotly.graph_objs as go
import pandas as pd
from dash.exceptions import PreventUpdate
from flask import send_file

def setup_logging():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'dashboard.log')
    log_format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    max_bytes = int(os.getenv('LOG_MAX_BYTES', 10485760))
    backup_count = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    logger = logging.getLogger('dashboard')
    logger.setLevel(getattr(logging, log_level))
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(getattr(logging, log_level))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

USERNAME = "Auther"
LOGO_PATH = "/assets/logo.png"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_FOLDER = os.path.join(BASE_DIR, "mdl", "input")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "mdl", "output")
TEMP_FOLDER = os.path.join(BASE_DIR, "mdl", "temp")
MAPPING_FILE = os.path.join(BASE_DIR, "mdl", "variable_mapping.json")

os.makedirs(DEFAULT_INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

logger.info(f"Dashboard initialized - Input: {DEFAULT_INPUT_FOLDER}, Output: {OUTPUT_FOLDER}")

def get_txt_files_from_folder(folder_path: str) -> List[str]:
    try:
        if not os.path.exists(folder_path):
            return []
        txt_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        return sorted(txt_files)
    except Exception as e:
        print(f"Error reading folder: {e}")
        return []


def get_case_insensitive_column(col_name, available_columns):
    col_lower = col_name.lower()
    for col in available_columns:
        if col.lower() == col_lower:
            return col
    return None


def get_case_insensitive_filepath(folder_path, filename):
    try:
        files_in_folder = os.listdir(folder_path)
        for file in files_in_folder:
            if file.lower() == filename.lower():
                return os.path.join(folder_path, file)
    except:
        pass
    return None


def get_column_names_from_txt(file_path: str) -> List[str]:
    try:
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        
        if first_line:
            columns = first_line.split('\t')
            return columns
        return []
    except Exception as e:
        print(f"Error reading columns: {e}")
        return []


def scan_txt_files_for_variables(folder_path: str) -> Dict[str, List[str]]:
    try:
        if not os.path.exists(folder_path):
            return {}
        
        variable_map = {}
        txt_files = get_txt_files_from_folder(folder_path)
        
        for txt_file in txt_files:
            file_path = os.path.join(folder_path, txt_file)
            columns = get_column_names_from_txt(file_path)
            
            for col in columns:
                if col not in variable_map:
                    variable_map[col] = []
                if txt_file not in variable_map[col]:
                    variable_map[col].append(txt_file)
        
        return dict(sorted(variable_map.items()))
    except Exception as e:
        print(f"Error scanning txt files: {e}")
        return {}


def load_variable_mapping() -> Dict[str, str]:
    try:
        if os.path.exists(MAPPING_FILE):
            with open(MAPPING_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading mapping: {e}")
        return {}


def save_variable_mapping(mapping: Dict[str, str]):
    try:
        with open(MAPPING_FILE, 'w') as f:
            json.dump(mapping, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving mapping: {e}")
        return False


def get_available_txt_files(folder_path: str) -> List[str]:
    return get_txt_files_from_folder(folder_path)


def copy_folder_structure(src: str, dest: str) -> bool:
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        
        os.makedirs(dest, exist_ok=True)
        
        for item in os.listdir(src):
            if item in ['__MACOSX', '.DS_Store', '.AppleDouble', '.AppleDB', 'input']:
                continue
            
            src_path = os.path.join(src, item)
            dest_path = os.path.join(dest, item)
            
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)
        
        return True
    except Exception as e:
        print(f"Error copying folder: {e}")
        return False


def modify_txt_file(file_path: str, modifications: List[Dict]) -> Tuple[bool, str, int]:
    try:
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return False, error_msg, 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            error_msg = f"File is empty: {file_path}"
            logger.warning(error_msg)
            return False, error_msg, 0
        
        header = lines[0].rstrip('\n').split('\t')
        
        for mod in modifications:
            if mod['column'] not in header:
                error_msg = f"Column '{mod['column']}' not found in {os.path.basename(file_path)}"
                logger.error(error_msg)
                return False, error_msg, 0
            for condition in mod.get('conditions', []):
                if condition['field'] not in header:
                    error_msg = f"Condition column '{condition['field']}' not found in {os.path.basename(file_path)}"
                    logger.error(error_msg)
                    return False, error_msg, 0
        
        col_indices = {}
        for idx, col in enumerate(header):
            if col not in col_indices:
                col_indices[col] = []
            col_indices[col].append(idx)
        
        for col in col_indices:
            if len(col_indices[col]) == 1:
                col_indices[col] = col_indices[col][0]
        
        logger.debug(f"Processing {os.path.basename(file_path)} with {len(modifications)} modifications")
        
        modified_count = 0
        for i in range(1, len(lines)):
            row = lines[i].rstrip('\n').split('\t')
            
            for mod in modifications:
                col_idx_data = col_indices[mod['column']]
                col_idx = col_idx_data[0] if isinstance(col_idx_data, list) else col_idx_data
                conditions = mod.get('conditions', [])
                
                should_modify = True
                if conditions:
                    for condition in conditions:
                        try:
                            field_name = condition['field']
                            if field_name not in col_indices:
                                should_modify = False
                                break
                            field_idx_data = col_indices[field_name]
                            field_idx = field_idx_data[0] if isinstance(field_idx_data, list) else field_idx_data
                            condition_value = condition['value']
                            
                            if field_idx >= len(row) or row[field_idx] != condition_value:
                                should_modify = False
                                break
                        except Exception as e:
                            logger.debug(f"Condition check failed: {str(e)}")
                            should_modify = False
                            break
                
                if should_modify:
                    if col_idx < len(row):
                        old_value = row[col_idx]
                        row[col_idx] = str(mod['value'])
                        logger.debug(f"Modified row {i}: {mod['column']} ({old_value} -> {mod['value']})")
                        modified_count += 1
            
            lines[i] = '\t'.join(row) + '\n'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        success_msg = f"Modified {modified_count} rows"
        logger.info(f"{os.path.basename(file_path)}: {success_msg}")
        return True, success_msg, modified_count
    
    except Exception as e:
        error_msg = f"Error modifying file: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg, 0


def create_batch_copies(
    source_folder: str,
    output_base_folder: str,
    num_copies: int,
    batch_name: str,
    modifications: Dict[str, List[Dict]]
) -> Tuple[bool, str, Dict]:
    try:
        if not os.path.exists(source_folder):
            error_msg = f"Source folder not found: {source_folder}"
            logger.error(error_msg)
            return False, error_msg, {}
        
        if num_copies < 1 or num_copies > 1000:
            error_msg = "Number of copies must be between 1 and 1000"
            logger.error(error_msg)
            return False, error_msg, {}
        
        logger.info(f"Creating batch '{batch_name}' with {num_copies} copies from {source_folder}")
        
        batch_folder = os.path.join(output_base_folder, batch_name)
        if os.path.exists(batch_folder):
            shutil.rmtree(batch_folder)
        os.makedirs(batch_folder, exist_ok=True)
        logger.info(f"Created batch folder: {batch_folder}")
        
        summary = {}
        errors = []
        
        for copy_num in range(1, num_copies + 1):
            copy_folder = os.path.join(batch_folder, f"{batch_name}_{copy_num}")
            
            if not copy_folder_structure(source_folder, copy_folder):
                error_msg = f"Failed to copy folder {copy_num}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
            
            logger.debug(f"Created copy {copy_num} at {copy_folder}")
            
            for txt_file, mods_list in modifications.items():
                for mod_spec in mods_list:
                    if mod_spec['copy'] == copy_num:
                        file_path = os.path.join(copy_folder, txt_file)
                        success, message, row_count = modify_txt_file(file_path, mod_spec['changes'])
                        
                        if not success:
                            error_msg = f"Copy {copy_num}: {message}"
                            errors.append(error_msg)
                            logger.error(error_msg)
                        else:
                            key = f"{txt_file} (Copy {copy_num})"
                            summary[key] = f"{message}"
                            logger.debug(f"Applied modifications to {txt_file} copy {copy_num}")
        
        if errors:
            error_msg = "; ".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"; ... and {len(errors) - 5} more errors"
            logger.warning(f"Batch created with errors: {error_msg}")
            return False, f"Batch created with errors: {error_msg}", summary
        
        success_msg = f"Successfully created {num_copies} copies in {batch_name}"
        logger.info(success_msg)
        return True, success_msg, summary
    
    except Exception as e:
        error_msg = f"Error creating batch: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg, {}


def run_cpp_model(folders: List[str], cpp_command: str) -> Tuple[bool, str, float, List[Dict]]:
    try:
        logger.info(f"Starting model execution on {len(folders)} folders")
        logger.debug(f"Command template: {cpp_command}")
        
        results = []
        total_time = 0
        
        for folder in folders:
            start_time = time.time()
            folder_name = os.path.basename(folder)
            
            cmd = cpp_command.replace("{folder}", folder)
            logger.info(f"Executing model on {folder_name}: {cmd}")
            
            try:
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=folder
                )
                stdout, stderr = process.communicate(timeout=3600)
                
                elapsed_time = time.time() - start_time
                total_time += elapsed_time
                
                success = process.returncode == 0
                results.append({
                    'folder': folder_name,
                    'runtime': elapsed_time,
                    'success': success,
                    'output': stdout.decode('utf-8', errors='ignore')[-500:],
                    'error': stderr.decode('utf-8', errors='ignore')[-500:]
                })
                
                status = "SUCCESS" if success else "FAILED"
                logger.info(f"{folder_name} {status} ({elapsed_time:.2f}s)")
                
                if not success and stderr:
                    logger.warning(f"{folder_name} error output: {stderr.decode('utf-8', errors='ignore')[:200]}")
            
            except subprocess.TimeoutExpired:
                elapsed_time = time.time() - start_time
                total_time += elapsed_time
                logger.error(f"{folder_name} timed out after {elapsed_time:.2f}s")
                results.append({
                    'folder': folder_name,
                    'runtime': elapsed_time,
                    'success': False,
                    'output': '',
                    'error': 'Model execution timed out (exceeded 3600 seconds)'
                })
        
        logger.info(f"Model execution complete. Total time: {total_time:.2f}s. Success: {sum(1 for r in results if r['success'])}/{len(results)}")
        return True, f"Model run completed in {total_time:.2f} seconds", total_time, results
    
    except Exception as e:
        error_msg = f"Error running model: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg, 0, []


def create_zip_from_folder(folder_path: str, zip_path: str) -> bool:
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print(f"Error creating ZIP: {e}")
        return False


app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Batch Generator & Model Runner"

@app.server.route('/download-batch/<path:batch_name>')
def download_batch(batch_name):
    batch_path = os.path.join(OUTPUT_FOLDER, batch_name)
    if not os.path.exists(batch_path):
        return "Batch not found", 404
    
    zip_path = os.path.join(TEMP_FOLDER, f"{batch_name}.zip")
    if create_zip_from_folder(batch_path, zip_path):
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{batch_name}.zip"
        )
    return "Error creating ZIP", 500


@app.server.route('/download-template')
def download_template():
    template_path = "/Users/example.xlsx"
    if not os.path.exists(template_path):
        return "Template file not found", 404
    
    return send_file(
        template_path,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='template.xlsx'
    )


app.layout = html.Div([
    html.Div(
        className='header',
        children=[
            html.Div(
                className='header-left',
                children=[
                    html.Img(
                        src=LOGO_PATH,
                        className='logo'
                    ),
                    html.H1("Sample", className='header-title', style={'color': 'black'})
                ]
            ),
            html.Div(
                className='header-right',
                children=f"{USERNAME}",
                style={'color': 'black'}
            )
        ]
    ),
    
    html.Div(
        className='container',
        children=[
            dcc.Store(id='batch-store', data={}),
            dcc.Store(id='model-results-store', data={}),
            dcc.Store(id='scenarios-store', data={}),
            dcc.Store(id='variables-mapping-store', data={}),
            dcc.Store(id='unmapped-variables-store', data={}),
            dcc.Store(id='table-data-store', data={
                'columns': ['"name.txt","condition/(s)", "new value" 1', '"name.txt","condition/(s)", "new value" 2'],
                'rows': [
                    {'"name.txt","condition/(s)", "new value" 1': '', '"name.txt","condition/(s)", "new value" 2': ''},
                    {'"name.txt","condition/(s)", "new value" 1': '', '"name.txt","condition/(s)", "new value" 2': ''}
                ]
            }),
            html.Div(id='app-init', style={'display': 'none'}),
            
            dcc.Tabs(
                id='main-tabs',
                value='tab-0',
                children=[
                    dcc.Tab(
                        label='Import Scenarios',
                        value='tab-0',
                        children=[
                            html.Div(className='tab-content', children=[
                                html.Div(style={'display': 'flex', 'alignItems': 'center', 'gap': '20px', 'marginBottom': '20px', 'justifyContent': 'space-between', 'flexWrap': 'wrap'}, children=[
                                    html.H2("Step 1: Import Excel Data", style={'margin': '0'}),
                                    html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}, children=[
                                        html.A(
                                            'Download Template',
                                            href='/download-template',
                                            className='button',
                                            target='_blank',
                                            style={'display': 'inline-block', 'padding': '10px 16px', 'fontSize': '14px', 'textDecoration': 'none', 'backgroundColor': '#2196F3', 'color': 'white', 'borderRadius': '4px', 'cursor': 'pointer'}
                                        ),
                                        html.Button(
                                            'Upload Input Folder',
                                            id='upload-folder-btn',
                                            className='button',
                                            style={'padding': '10px 16px', 'fontSize': '14px'}
                                        )
                                    ])
                                ]),
                                
                                html.Div(style={'marginBottom': '15px'}, children=[
                                    dcc.Upload(
                                        id='folder-upload-zip',
                                        children=html.Div('Drag and Drop ZIP File or Click to Select', style={'textAlign': 'center', 'padding': '10px', 'color': '#999', 'fontSize': '13px'}),
                                        style={
                                            'width': '100%',
                                            'height': '0px',
                                            'lineHeight': '0px',
                                            'borderWidth': '0px',
                                            'display': 'none',
                                            'overflow': 'hidden'
                                        },
                                        accept='.zip',
                                        multiple=False
                                    )
                                ]),
                                
                                html.Div(style={'marginBottom': '15px'}, children=[
                                    dcc.Upload(
                                        id='folder-upload-direct',
                                        children=html.Div('Drag and Drop Folder or Click to Select (Chrome/Edge/Firefox)', style={'textAlign': 'center', 'padding': '10px', 'color': '#999', 'fontSize': '13px'}),
                                        style={
                                            'width': '100%',
                                            'height': '0px',
                                            'lineHeight': '0px',
                                            'borderWidth': '0px',
                                            'display': 'none',
                                            'overflow': 'hidden'
                                        },
                                        multiple=True
                                    )
                                ]),
                                
                                html.Div(id='folder-upload-status', style={'marginBottom': '15px', 'fontSize': '14px'}),
                                
                                html.Div(id='txt-files-list', style={'marginBottom': '20px'}),
                                
                                html.Div(style={'marginBottom': '20px'}, children=[
                                    dcc.Upload(
                                        id='excel-upload',
                                        children=html.Div([
                                            'Drag and Drop or ',
                                            html.A('Click to Select Excel File')
                                        ]),
                                        style={
                                            'width': '100%',
                                            'height': '60px',
                                            'lineHeight': '60px',
                                            'borderWidth': '2px',
                                            'borderStyle': 'dashed',
                                            'borderRadius': '4px',
                                            'textAlign': 'center',
                                            'cursor': 'pointer',
                                            'backgroundColor': '#f9f9f9'
                                        },
                                        accept='.xlsx,.xls,.csv'
                                    ),
                                ]),
                                
                                html.Div(id='upload-status', style={'marginBottom': '15px', 'fontSize': '14px'}),
                                
                                html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '15px', 'justifyContent': 'space-between', 'alignItems': 'center'}, children=[
                                    html.H3("Scenarios", style={'margin': '0'}),
                                    html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}, children=[
                                        html.Button('Add Row', id='add-row-btn', className='button', n_clicks=0),
                                        html.Button('Add Column', id='add-col-btn', className='button', n_clicks=0),
                                        html.Div(style={'display': 'flex', 'gap': '10px', 'alignItems': 'center'}, children=[
                                            html.Label("Delete column:", style={'fontSize': '13px', 'fontWeight': 'bold'}),
                                            dcc.Dropdown(
                                                id='delete-col-dropdown',
                                                placeholder='Select column',
                                                style={'width': '150px', 'fontSize': '13px'},
                                                clearable=False
                                            ),
                                            html.Button('✕', id='delete-col-btn', className='button', n_clicks=0,
                                                       style={'padding': '6px 12px', 'backgroundColor': '#d32f2f', 'color': 'white', 'border': 'none'})
                                        ])
                                    ])
                                ]),
                                
                                html.P("Each row is one scenario. Edit cells directly or upload Excel file above.", style={'color': '#666', 'fontSize': '13px', 'marginBottom': '15px'}),
                                
                                html.Div(id='scenarios-data-table', style={'marginBottom': '20px', 'overflowX': 'auto'}),
                                
                                html.Div(style={'display': 'flex', 'gap': '10px', 'marginTop': '15px', 'marginBottom': '20px', 'alignItems': 'center', 'flexWrap': 'wrap'}, children=[
                                    html.Button(
                                        'Parse Scenarios',
                                        id='parse-excel-btn',
                                        className='button',
                                        n_clicks=0
                                    ),
                                    html.Div(id='parse-status', style={'display': 'flex', 'alignItems': 'center', 'fontSize': '14px'})
                                ]),
                                
                                html.Div(id='excel-preview-table', style={'marginBottom': '20px', 'overflowX': 'auto'}),
                                
                                html.H2("Step 2: Review Scenarios"),
                                html.Div(id='scenarios-table', style={'marginBottom': '20px'}),
                                
                                html.Div(id='scenario-editor-modal', style={'marginTop': '30px'}),
                                
                                html.Div(style={'display': 'flex', 'gap': '15px', 'alignItems': 'center', 'marginTop': '30px', 'marginBottom': '20px'}, children=[
                                    html.Div(children=[
                                        html.Label("Batch name:", className='input-label'),
                                        dcc.Input(
                                            id='batch-name-input',
                                            type='text',
                                            placeholder='e.g., batch_scenarios',
                                            value='batch_scenarios',
                                            className='input-field',
                                            style={'width': '250px', 'padding': '12px', 'fontSize': '14px', 'height': '40px'}
                                        )
                                    ]),
                                    html.Button(
                                        'Create Batch',
                                        id='create-batch-btn',
                                        className='button',
                                        style={'marginTop': '25px', 'fontSize': '14px', 'padding': '10px 20px'}
                                    )
                                ]),
                                
                                html.Div(id='batch-message', style={'marginTop': '20px'}),
                                html.Div(id='batch-summary', style={'marginTop': '20px'}),
                                html.Div(id='download-batch-container', style={'marginTop': '20px'}),
                                
                                dcc.Store(id='scenarios-store', data={}),
                            ])
                        ]
                    ),
                    
                    dcc.Tab(
                        label='Run Model',
                        value='tab-1',
                        children=[
                            html.Div(className='tab-content', children=[
                                html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '20px'}, children=[
                                    html.H2("Select Batch to Run", style={'margin': '0'}),
                                    html.Button(
                                        'Run Model',
                                        id='run-model-btn',
                                        className='button',
                                        style={'fontSize': '14px', 'padding': '10px 20px', 'height': 'fit-content'}
                                    )
                                ]),
                                html.Div(className='input-group', children=[
                                    html.Label("Batch folder:", className='input-label'),
                                    dcc.Dropdown(
                                        id='batch-dropdown',
                                        options=[],
                                        placeholder='Select a batch...',
                                        style={'width': '100%'}
                                    )
                                ]),
                                
                                html.H2("Configure Model Command"),
                                html.Div(className='input-group', children=[
                                    html.Label("C++ model command:", className='input-label'),
                                    dcc.Input(
                                        id='cpp-command-input',
                                        type='text',
                                        placeholder='./spire_test dfc "{folder}" "/output/path"',
                                        value='./spire_test dfc "/path/to/input" "/path/to/output"',
                                        className='input-field',
                                        style={'width': '100%', 'height': '45px', 'padding': '12px', 'fontSize': '14px'}
                                    )
                                ]),
                                
                                html.Div(id='model-status', style={'marginTop': '20px'}),
                                html.Div(id='model-progress', style={'marginTop': '20px'}),
                                html.Div(id='model-summary', style={'marginTop': '20px'}),
                                html.Div(id='download-output-container', style={'marginTop': '20px'})
                            ])
                        ]
                    )
                ]
            )
        ]
    )
])


@app.callback(
    Output('folder-upload-zip', 'style'),
    Output('folder-upload-direct', 'style'),
    Input('upload-folder-btn', 'n_clicks'),
    State('folder-upload-zip', 'style'),
    State('folder-upload-direct', 'style'),
    prevent_initial_call=True
)
def toggle_folder_upload(n_clicks, zip_style, direct_style):
    for style in [zip_style, direct_style]:
        if style.get('display') == 'none':
            style['display'] = 'block'
            style['height'] = '60px'
            style['lineHeight'] = '60px'
            style['borderWidth'] = '2px'
            style['borderStyle'] = 'dashed'
            style['borderRadius'] = '4px'
            style['textAlign'] = 'center'
            style['cursor'] = 'pointer'
            style['backgroundColor'] = '#f9f9f9'
        else:
            style['display'] = 'none'
            style['height'] = '0px'
            style['lineHeight'] = '0px'
            style['borderWidth'] = '0px'
    return zip_style, direct_style


@app.callback(
    Output('folder-upload-status', 'children'),
    Input('folder-upload-zip', 'contents'),
    Input('folder-upload-direct', 'contents'),
    State('folder-upload-zip', 'filename'),
    State('folder-upload-direct', 'filename'),
    prevent_initial_call=True
)
def handle_folder_upload(zip_contents, direct_contents, zip_filename, direct_filenames):
    
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if triggered_id == 'folder-upload-zip':
            if zip_contents is None:
                raise PreventUpdate
            
            content_type, content_string = zip_contents.split(',')
            decoded = base64.b64decode(content_string)
            
            temp_zip = os.path.join(TEMP_FOLDER, 'temp_folder.zip')
            with open(temp_zip, 'wb') as f:
                f.write(decoded)
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(DEFAULT_INPUT_FOLDER)
            
            for item in os.listdir(DEFAULT_INPUT_FOLDER):
                if item in ['__MACOSX', '.DS_Store', '.AppleDouble', '.AppleDB']:
                    item_path = os.path.join(DEFAULT_INPUT_FOLDER, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
            
            os.remove(temp_zip)
            
            logger.info(f"ZIP input folder uploaded and extracted: {zip_filename}")
            return html.Div(
                f"ZIP file '{zip_filename}' uploaded and extracted successfully to {DEFAULT_INPUT_FOLDER}!",
                style={'color': '#4caf50', 'fontSize': '14px', 'fontWeight': 'bold'}
            )
        
        elif triggered_id == 'folder-upload-direct':
            if direct_contents is None:
                raise PreventUpdate
            
            if not isinstance(direct_contents, list):
                raise ValueError("Expected list of files from folder upload")
            
            if not direct_filenames or not isinstance(direct_filenames, list):
                raise ValueError("No files received from folder upload")
            
            file_count = 0
            for content, filename in zip(direct_contents, direct_filenames):
                if content is None:
                    continue
                
                try:
                    content_type, content_string = content.split(',')
                    decoded = base64.b64decode(content_string)
                    
                    file_path = os.path.join(DEFAULT_INPUT_FOLDER, filename.lstrip('/'))
                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'wb') as f:
                        f.write(decoded)
                    
                    file_count += 1
                    logger.debug(f"Extracted file: {filename}")
                
                except Exception as e:
                    logger.warning(f"Error processing file {filename}: {str(e)}")
                    continue
            
            if file_count == 0:
                raise ValueError("No files were successfully extracted from the folder")
            
            logger.info(f"Folder uploaded and extracted {file_count} files")
            return html.Div(
                f"Folder uploaded successfully with {file_count} files extracted to {DEFAULT_INPUT_FOLDER}!",
                style={'color': '#4caf50', 'fontSize': '14px', 'fontWeight': 'bold'}
            )
        
        else:
            raise PreventUpdate
    
    except Exception as e:
        error_msg = f"Error uploading folder: {str(e)}"
        logger.error(error_msg)
        return html.Div(
            f"{error_msg}",
            style={'color': '#d32f2f', 'fontSize': '14px'}
        )


@app.callback(
    Output('txt-files-list', 'children'),
    Input('folder-upload-status', 'children'),
    prevent_initial_call=False
)
def display_txt_files(_):
    if not os.path.exists(DEFAULT_INPUT_FOLDER):
        return html.Div()
    
    try:
        txt_files = get_txt_files_from_folder(DEFAULT_INPUT_FOLDER)
        
        if not txt_files:
            return html.Div()
        
        file_items = []
        for txt_file in txt_files:
            file_items.append(
                html.Div(
                    txt_file,
                    style={'padding': '6px 12px', 'backgroundColor': '#e3f2fd', 'marginRight': '8px', 'borderRadius': '3px', 'fontSize': '13px', 'fontFamily': 'monospace', 'border': '1px solid #2196F3', 'display': 'inline-block'}
                )
            )
        
        return html.Div(
            children=[
                html.H4("Available Input Files", style={'marginBottom': '10px', 'color': '#333', 'fontSize': '14px'}),
                html.Div(file_items, style={'padding': '10px', 'backgroundColor': '#fafafa', 'borderRadius': '4px', 'border': '1px solid #e0e0e0', 'whiteSpace': 'nowrap', 'overflowX': 'auto', 'display': 'flex', 'flexWrap': 'wrap', 'gap': '8px'})
            ],
            style={'marginBottom': '20px'}
        )
    except Exception as e:
        logger.warning(f"Error displaying txt files: {str(e)}")
        return html.Div()


@app.callback(
    Output('scenarios-store', 'data'),
    Output('excel-preview-table', 'children'),
    Output('parse-status', 'children'),
    Input('parse-excel-btn', 'n_clicks'),
    State('table-data-store', 'data'),
    prevent_initial_call=True
)
def handle_excel_parse(n_clicks, table_data):
    if not table_data or not table_data.get('rows'):
        return {}, html.Div(), html.Div("No data to parse", className='message error')
    
    folder_path = DEFAULT_INPUT_FOLDER
    if not os.path.exists(folder_path):
        return {}, html.Div(), html.Div(f"Input folder not found: {folder_path}", className='message error')
    
    try:
        rows = table_data['rows']
        scenarios = {}
        errors = []
        
        for row_idx, row in enumerate(rows, 1):
            scenario_data = {}
            
            for col_name, cell_value in row.items():
                cell = str(cell_value).strip() if cell_value else ""
                if not cell:
                    continue
                
                try:
                    parts = []
                    in_quotes = False
                    current = ""
                    for char in cell:
                        if char == '"':
                            in_quotes = not in_quotes
                        elif char == ',' and not in_quotes:
                            parts.append(current.strip().strip('"'))
                            current = ""
                        else:
                            current += char
                    if current:
                        parts.append(current.strip().strip('"'))
                    
                    if len(parts) < 2:
                        continue
                    
                    filename = parts[0].strip()
                    
                    if len(parts) == 2:
                        condition = ""
                        new_value_str = parts[1].strip()
                    elif len(parts) >= 3:
                        condition = parts[1].strip()
                        new_value_str = parts[2].strip()
                    
                    if not filename.endswith('.txt'):
                        filename += '.txt'
                    
                    file_path = get_case_insensitive_filepath(folder_path, filename)
                    if not file_path:
                        errors.append(f"Row {row_idx}: File '{filename}' not found in input folder")
                        continue
                    
                    if '=' not in new_value_str:
                        errors.append(f"Row {row_idx}: Invalid format in cell. Expected 'column=value' but got '{new_value_str}'")
                        continue
                    
                    col_name_parsed, col_value = new_value_str.split('=', 1)
                    col_name_parsed = col_name_parsed.strip()
                    col_value = col_value.strip()
                    
                    try:
                        file_columns = get_column_names_from_txt(file_path)
                        actual_col_name = get_case_insensitive_column(col_name_parsed, file_columns)
                        if not actual_col_name:
                            errors.append(f"Row {row_idx}: Column '{col_name_parsed}' not found in '{filename}'. Available columns: {', '.join(file_columns)}")
                            continue
                        col_name_parsed = actual_col_name
                    except Exception as e:
                        errors.append(f"Row {row_idx}: Error reading '{filename}': {str(e)}")
                        continue
                    
                    if filename not in scenario_data:
                        scenario_data[filename] = []
                    
                    mod = {
                        'column': col_name_parsed,
                        'value': col_value,
                        'conditions': []
                    }
                    
                    if condition:
                        and_parts = re.split(r'\s+and\s+', condition, flags=re.IGNORECASE)
                        
                        for and_part in and_parts:
                            and_part = and_part.strip()
                            or_parts = re.split(r'\s+or\s+', and_part, flags=re.IGNORECASE)
                            
                            for or_part in or_parts:
                                or_part = or_part.strip()
                                if '=' in or_part:
                                    cond_field, cond_value = or_part.split('=', 1)
                                    mod['conditions'].append({
                                        'field': cond_field.strip(),
                                        'value': cond_value.strip()
                                    })
                    
                    scenario_data[filename].append(mod)
                
                except Exception as e:
                    errors.append(f"Row {row_idx}, Column {col_name}: Error parsing - {str(e)}")
                    continue
            
            if scenario_data:
                scenarios[f"scenario_{row_idx}"] = {
                    'id': f"scenario_{row_idx}",
                    'name': f"Scenario {row_idx}",
                    'modifications': scenario_data
                }
        
        if errors:
            error_text = "ERRORS FOUND:\n\n" + "\n".join(errors)
            error_message = html.Div(
                html.Pre(error_text, style={'whiteSpace': 'pre-wrap', 'wordWrap': 'break-word', 'color': '#d32f2f', 'backgroundColor': '#ffebee', 'padding': '15px', 'borderRadius': '4px', 'fontSize': '13px'}),
                className='message error',
                style={'marginBottom': '20px'}
            )
            return scenarios, error_message, html.Div("Errors found - see details above", className='message error', style={'marginTop': '15px'})
        
        if not scenarios:
            return {}, html.Div(), html.Div("No valid scenarios parsed. Check your data format.", className='message error')
        
        return scenarios, html.Div(), html.Div(f"Parsed {len(scenarios)} scenarios successfully!", className='message success', style={'marginTop': '15px', 'color': '#4caf50', 'fontWeight': 'bold'})
    
    except Exception as e:
        return {}, html.Div(), html.Div(f"Error parsing data: {str(e)}", className='message error')


@app.callback(
    Output('scenarios-table', 'children'),
    Input('scenarios-store', 'data'),
    prevent_initial_call=False
)
def display_scenarios_table(scenarios):
    if not scenarios:
        return html.Div()
    
    rows = []
    for scenario_id, scenario in scenarios.items():
        total_mods = sum(len(mods) for mods in scenario['modifications'].values())
        files_count = len(scenario['modifications'])
        files_list = ", ".join(scenario['modifications'].keys())
        
        rows.append(html.Tr([
            html.Td(scenario['name'], style={'fontWeight': '600'}),
            html.Td(files_count),
            html.Td(total_mods),
            html.Td(files_list, style={'color': '#666', 'fontSize': '12px'}),
            html.Td(
                html.Button(
                    'Edit',
                    id={'type': 'edit-scenario-btn', 'index': scenario_id},
                    className='button',
                    style={'fontSize': '12px', 'padding': '6px 12px'}
                ),
                style={'whiteSpace': 'nowrap'}
            )
        ]))
    
    table = html.Table(
        className='summary-table',
        children=[
            html.Thead(html.Tr([
                html.Th("Scenario"),
                html.Th("Files"),
                html.Th("Modifications"),
                html.Th("File Details"),
                html.Th("Actions")
            ])),
            html.Tbody(rows)
        ]
    )
    
    return table


@app.callback(
    Output('scenario-editor-modal', 'children'),
    Input({'type': 'edit-scenario-btn', 'index': ALL}, 'n_clicks'),
    State('scenarios-store', 'data'),
    State('variables-mapping-store', 'data'),
    prevent_initial_call=True
)
def edit_scenario_modal(n_clicks, scenarios, variables_map):
    if not scenarios or not variables_map or not n_clicks or not any(n_clicks):
        return html.Div()
    
    callback_context = dash.callback_context
    if not callback_context.triggered:
        return html.Div()
    
    scenario_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    scenario_id = json.loads(scenario_id)['index']
    
    if scenario_id not in scenarios:
        return html.Div()
    
    scenario = scenarios[scenario_id]
    
    editor_sections = []
    
    for txt_file, modifications in scenario['modifications'].items():
        mod_rows = []
        for mod_idx, mod in enumerate(modifications):
            mod_rows.append(
                html.Div(style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'marginBottom': '10px', 'borderRadius': '4px'}, children=[
                    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr auto', 'gap': '10px', 'alignItems': 'center'}, children=[
                        html.Div([
                            html.Strong(mod['variable']),
                            html.Div(f"Value: {mod['value']}", style={'fontSize': '12px', 'color': '#666'})
                        ]),
                        html.Div(
                            f"Conditions: {len(mod.get('conditions', []))}",
                            style={'fontSize': '12px', 'color': '#666', 'padding': '5px', 'backgroundColor': '#eee', 'borderRadius': '3px'}
                        ),
                        html.Button(
                            'Edit',
                            className='button',
                            style={'fontSize': '11px', 'padding': '4px 8px'}
                        )
                    ])
                ])
            )
        
        editor_sections.append(
            html.Div(style={'marginBottom': '20px', 'padding': '15px', 'border': '1px solid #ddd', 'borderRadius': '4px'}, children=[
                html.H4(txt_file, style={'margin': '0 0 15px 0', 'color': '#333'}),
                html.Div(mod_rows)
            ])
        )
    
    return html.Div(
        style={'marginTop': '20px', 'padding': '20px', 'backgroundColor': '#f5f5f5', 'borderRadius': '4px', 'border': '2px solid #ddd'},
        children=[
            html.H3(f"Edit {scenario['name']}", style={'margin': '0 0 20px 0'}),
            html.Div(editor_sections),
            html.Div(style={'display': 'flex', 'gap': '10px', 'marginTop': '20px'}, children=[
                html.Button('Save Changes', className='button', style={'fontSize': '14px', 'padding': '10px 20px'}),
                html.Button('Cancel', className='button secondary', style={'fontSize': '14px', 'padding': '10px 20px'})
            ])
        ]
    )


@app.callback(
    Output('mappings-management', 'children'),
    Input('app-init', 'children'),
    prevent_initial_call=False
)
def display_mappings_table(_):
    mapping = load_variable_mapping()
    
    if not mapping:
        return html.Div("No saved mappings yet. Mappings will be created as you parse Excel data.", 
                       style={'fontStyle': 'italic', 'color': '#999', 'padding': '10px'})
    
    rows = []
    for var_name in sorted(mapping.keys()):
        file_name = mapping[var_name]
        rows.append(html.Tr([
            html.Td(var_name, style={'fontWeight': '600'}),
            html.Td(file_name, style={'color': '#666'}),
            html.Td(
                html.Button('Delete', 
                           id={'type': 'delete-mapping-btn', 'index': var_name},
                           className='button small',
                           n_clicks=0,
                           style={'padding': '4px 8px', 'fontSize': '12px'}),
                style={'textAlign': 'center'}
            )
        ]))
    
    table = html.Table(
        className='summary-table',
        children=[
            html.Thead(html.Tr([
                html.Th("Variable"),
                html.Th("File"),
                html.Th("Action")
            ])),
            html.Tbody(rows)
        ]
    )
    
    return table


@app.callback(
    Output('mappings-management', 'children', allow_duplicate=True),
    Input({'type': 'delete-mapping-btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'delete-mapping-btn', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def delete_mapping(n_clicks_list, btn_ids):
    if not any(n_clicks_list):
        return html.Div()
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = eval(button_id)
    var_name = button_data['index']
    
    mapping = load_variable_mapping()
    if var_name in mapping:
        del mapping[var_name]
        save_variable_mapping(mapping)
    
    rows = []
    for vn in sorted(mapping.keys()):
        file_name = mapping[vn]
        rows.append(html.Tr([
            html.Td(vn, style={'fontWeight': '600'}),
            html.Td(file_name, style={'color': '#666'}),
            html.Td(
                html.Button('Delete', 
                           id={'type': 'delete-mapping-btn', 'index': vn},
                           className='button small',
                           n_clicks=0,
                           style={'padding': '4px 8px', 'fontSize': '12px'}),
                style={'textAlign': 'center'}
            )
        ]))
    
    if not rows:
        return html.Div("No saved mappings yet.", style={'fontStyle': 'italic', 'color': '#999', 'padding': '10px'})
    
    table = html.Table(
        className='summary-table',
        children=[
            html.Thead(html.Tr([
                html.Th("Variable"),
                html.Th("File"),
                html.Th("Action")
            ])),
            html.Tbody(rows)
        ]
    )
    
    return table


@app.callback(
    Output('batch-message', 'children'),
    Output('batch-summary', 'children'),
    Output('batch-store', 'data'),
    Output('download-batch-container', 'children'),
    Input('create-batch-btn', 'n_clicks'),
    State('batch-name-input', 'value'),
    State('scenarios-store', 'data'),
    prevent_initial_call=True
)
def create_batch_from_scenarios(n_clicks, batch_name, scenarios):
    
    logger.info(f"Create batch requested: {batch_name} with {len(scenarios) if scenarios else 0} scenarios")
    
    if not batch_name:
        logger.warning("Batch creation failed: no batch name provided")
        return html.Div("Please enter a batch name", className='message error'), html.Div(), {}, html.Div()
    
    if not scenarios:
        logger.warning("Batch creation failed: no scenarios available")
        return html.Div("No scenarios to create batch from. Parse Excel data first.", className='message error'), html.Div(), {}, html.Div()
    
    input_folder = DEFAULT_INPUT_FOLDER
    if not os.path.exists(input_folder):
        logger.error(f"Batch creation failed: input folder not found at {input_folder}")
        return html.Div(f"Invalid input folder: {input_folder}", className='message error'), html.Div(), {}, html.Div()
    
    try:
        modifications = {}
        for scenario_id, scenario in scenarios.items():
            for txt_file, mods in scenario['modifications'].items():
                if txt_file not in modifications:
                    modifications[txt_file] = []
                
                scenario_num = int(scenario_id.split('_')[1])
                
                modifications[txt_file].append({
                    'copy': scenario_num,
                    'changes': mods
                })
        
        success, message_text, summary = create_batch_copies(
            source_folder=input_folder,
            output_base_folder=OUTPUT_FOLDER,
            num_copies=len(scenarios),
            batch_name=batch_name,
            modifications=modifications
        )
        
        if success:
            logger.info(f"Batch '{batch_name}' created successfully with {len(scenarios)} copies")
            message = html.Div(
                message_text,
                className='message success'
            )
        else:
            logger.error(f"Batch '{batch_name}' creation failed: {message_text}")
            message = html.Div(
                message_text,
                className='message error'
            )
        
        summary_html = html.Div()
        if summary:
            rows = []
            for k, v in summary.items():
                rows.append(html.Tr([html.Td(k), html.Td(v)]))
            
            summary_html = html.Div(
                style={'maxHeight': '300px', 'overflowY': 'auto', 'border': '1px solid #ddd', 'borderRadius': '4px'},
                children=[
                    html.Table(
                        className='summary-table',
                        children=[
                            html.Thead(html.Tr([
                                html.Th("File & Copy"),
                                html.Th("Status")
                            ])),
                            html.Tbody(rows)
                        ],
                        style={'width': '100%'}
                    )
                ]
            )
        
        batch_path = os.path.join(OUTPUT_FOLDER, batch_name)
        download_html = html.Div()
        if success and os.path.exists(batch_path):
            download_html = html.Div([
                html.A(
                    'Download Batch as ZIP',
                    href=f'/download-batch/{batch_name}',
                    className='button',
                    target='_blank',
                    style={'display': 'inline-block', 'marginRight': '10px'}
                ),
                html.Span(f"Batch location: {batch_path}", style={'color': '#666'})
            ])
        
        return message, summary_html, {'batch_path': batch_path, 'batch_name': batch_name}, download_html
    
    except Exception as e:
        logger.exception(f"Exception while creating batch '{batch_name}': {str(e)}")
        return html.Div(f"Error creating batch: {str(e)}", className='message error'), html.Div(), {}, html.Div()


@app.callback(
    Output('batch-dropdown', 'options'),
    Input('batch-store', 'data'),
    prevent_initial_call=False
)
def update_batch_dropdown(batch_data):
    if os.path.exists(OUTPUT_FOLDER):
        batches = [d for d in os.listdir(OUTPUT_FOLDER) if os.path.isdir(os.path.join(OUTPUT_FOLDER, d))]
        return [{'label': b, 'value': os.path.join(OUTPUT_FOLDER, b)} for b in sorted(batches, reverse=True)]
    return []


@app.callback(
    Output('model-status', 'children'),
    Output('model-summary', 'children'),
    Output('model-results-store', 'data'),
    Input('run-model-btn', 'n_clicks'),
    State('batch-dropdown', 'value'),
    State('cpp-command-input', 'value'),
    prevent_initial_call=True
)
def run_model(n_clicks, batch_path, cpp_command):
    
    if not batch_path or not cpp_command:
        message = html.Div(
            "Please select a batch and provide a C++ command",
            className='message error'
        )
        return message, html.Div(), {}
    
    if not os.path.exists(batch_path):
        message = html.Div(
            f"Batch path not found: {batch_path}",
            className='message error'
        )
        return message, html.Div(), {}
    
    copy_folders = sorted([
        os.path.join(batch_path, d) for d in os.listdir(batch_path)
        if os.path.isdir(os.path.join(batch_path, d))
    ])
    
    if not copy_folders:
        message = html.Div(
            "No copies found in batch",
            className='message error'
        )
        return message, html.Div(), {}
    
    success, message_text, total_time, results = run_cpp_model(copy_folders, cpp_command)
    
    if success:
        final_message = html.Div(
            message_text,
            className='message success'
        )
    else:
        final_message = html.Div(
            message_text,
            className='message error'
        )
    
    summary_html = html.Div()
    if results:
        summary_rows = []
        for r in results:
            status = "Success" if r['success'] else "Failed"
            status_color = "#28a745" if r['success'] else "#dc3545"
            summary_rows.append(html.Tr([
                html.Td(r['folder']),
                html.Td(f"{r['runtime']:.2f}s"),
                html.Td(status, style={'color': status_color, 'fontWeight': 'bold'})
            ]))
        
        summary_html = html.Div([
            html.H3(f"Total Runtime: {total_time:.2f} seconds", style={'color': '#333'}),
            html.H4(f"Processed {len(results)} copies", style={'color': '#666'}),
            html.Table(
                className='summary-table',
                children=[
                    html.Thead(html.Tr([
                        html.Th("Copy Folder"),
                        html.Th("Runtime"),
                        html.Th("Status")
                    ])),
                    html.Tbody(summary_rows)
                ]
            )
        ])
    
    return final_message, summary_html, {'results': results, 'total_time': total_time}


def parse_excel_file(contents, filename):
    if contents is None:
        return None, "No file provided"
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        filename_lower = filename.lower()
        
        try:
            if 'csv' in filename_lower:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename_lower:
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return None, f"Unsupported file format: {filename}. Please use .xlsx, .xls, or .csv"
        except pd.errors.EmptyDataError:
            return None, "File is empty"
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
        
        if df.empty:
            return None, "File contains no data"
        
        columns = df.columns.tolist()
        
        if 'input_i' in columns:
            df = df.rename(columns={'input_i': 'Index'})
            columns = df.columns.tolist()
        
        rows = df.to_dict('records')
        
        return {'columns': columns, 'rows': rows}, None
    except Exception as e:
        error_msg = f"Error parsing file: {str(e)}"
        print(error_msg)
        return None, error_msg


@app.callback(
    Output('table-data-store', 'data', allow_duplicate=True),
    Output('upload-status', 'children'),
    Input('excel-upload', 'contents'),
    State('excel-upload', 'filename'),
    State('table-data-store', 'data'),
    prevent_initial_call=True
)
def handle_excel_upload(contents, filename, table_data):
    if contents is None:
        raise PreventUpdate
    
    parsed, error_msg = parse_excel_file(contents, filename)
    if parsed:
        excel_cols = parsed['columns']
        has_index = "Index" in excel_cols
        
        if table_data and table_data.get('columns'):
            current_columns = table_data['columns'].copy()
            new_rows = []
            
            new_columns = []
            
            if has_index:
                new_columns.append("Index")
            
            scenario_cols_from_excel = [col for col in excel_cols if col.startswith('"name.txt"')]
            scenario_cols_from_table = [col for col in current_columns if col.startswith('"name.txt"')]
            
            if scenario_cols_from_excel:
                new_columns.extend(scenario_cols_from_excel)
            else:
                new_columns.extend(scenario_cols_from_table)
            
            for excel_row in parsed['rows']:
                new_row = {}
                for new_col_name in new_columns:
                    if new_col_name in excel_cols:
                        new_row[new_col_name] = excel_row.get(new_col_name, '')
                    else:
                        new_row[new_col_name] = ''
                new_rows.append(new_row)
            
            for col in current_columns:
                if col not in new_columns:
                    new_columns.append(col)
                    for row in new_rows:
                        row[col] = ''
            
            return {
                'columns': new_columns,
                'rows': new_rows
            }, html.Div(f"Loaded {filename} ({len(new_rows)} rows into existing columns)", 
                       style={'color': '#4caf50', 'fontSize': '14px', 'fontWeight': 'bold'})
        else:
            return parsed, html.Div(f"Loaded {filename} ({len(parsed['rows'])} rows, {len(parsed['columns'])} columns)", 
                                   style={'color': '#4caf50', 'fontSize': '14px', 'fontWeight': 'bold'})
    else:
        error_display = error_msg if error_msg else "Error loading file"
        return {'columns': [], 'rows': []}, html.Div(f"{error_display}", 
                                                      style={'color': '#d32f2f', 'fontSize': '14px'})


@app.callback(
    Output('scenarios-data-table', 'children'),
    Input('table-data-store', 'data')
)
def update_scenarios_table(table_data):
    if not table_data or not table_data.get('columns'):
        return html.Div("No data. Upload a file or add rows.", style={'color': '#999'})
    
    columns = [{'name': col, 'id': col, 'editable': True} for col in table_data['columns']]
    
    return dash_table.DataTable(
        id='scenarios-editable-table',
        columns=columns,
        data=table_data['rows'],
        editable=True,
        row_deletable=True,
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '13px',
            'border': '1px solid #ddd'
        },
        style_header={
            'backgroundColor': '#b0c4de',
            'fontWeight': 'bold',
            'border': '1px solid #999'
        },
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f9f9f9'}
        ]
    )


@app.callback(
    Output('table-data-store', 'data', allow_duplicate=True),
    Input('scenarios-editable-table', 'data'),
    State('table-data-store', 'data'),
    prevent_initial_call=True
)
def save_table_edits(rows, table_data):
    if rows is not None and table_data:
        table_data['rows'] = rows
        return table_data
    raise PreventUpdate


@app.callback(
    Output('table-data-store', 'data', allow_duplicate=True),
    Input('add-row-btn', 'n_clicks'),
    State('table-data-store', 'data'),
    prevent_initial_call=True
)
def add_row(n_clicks, table_data):
    if not table_data or not table_data.get('columns'):
        return table_data
    
    new_row = {col: '' for col in table_data['columns']}
    table_data['rows'].append(new_row)
    return table_data


@app.callback(
    Output('table-data-store', 'data', allow_duplicate=True),
    Input('add-col-btn', 'n_clicks'),
    State('table-data-store', 'data'),
    prevent_initial_call=True
)
def add_column(n_clicks, table_data):
    if not table_data:
        return table_data
    
    col_num = len(table_data['columns']) + 1
    new_col = f'"name.txt","condition/(s)", "new value" {col_num}'
    
    table_data['columns'].append(new_col)
    for row in table_data['rows']:
        row[new_col] = ''
    
    return table_data


@app.callback(
    Output('delete-col-dropdown', 'options'),
    Input('table-data-store', 'data')
)
def update_delete_dropdown(table_data):
    if not table_data or not table_data.get('columns'):
        return []
    return [{'label': col, 'value': col} for col in table_data['columns']]


@app.callback(
    Output('table-data-store', 'data', allow_duplicate=True),
    Input('delete-col-btn', 'n_clicks'),
    State('delete-col-dropdown', 'value'),
    State('table-data-store', 'data'),
    prevent_initial_call=True
)
def delete_column(n_clicks, col_to_delete, table_data):
    if not col_to_delete or not table_data or col_to_delete not in table_data['columns']:
        raise PreventUpdate
    
    table_data['columns'].remove(col_to_delete)
    for row in table_data['rows']:
        if col_to_delete in row:
            del row[col_to_delete]
    
    return table_data


if __name__ == '__main__':
    debug_mode = os.getenv('DASH_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 8050))
    
    logger.info("=" * 60)
    logger.info("Starting Batch Generator & Model Runner Dashboard")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Port: {port}")
    logger.info(f"Input folder: {DEFAULT_INPUT_FOLDER}")
    logger.info(f"Output folder: {OUTPUT_FOLDER}")
    logger.info("=" * 60)
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
