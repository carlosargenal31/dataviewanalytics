from django.shortcuts import render
from .models import DataFile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import DataFile, DataRecord
from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404

from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from bson import ObjectId



def index(request):
    return render(request, 'home/index.html')

def index(request, file_id=None):
    if file_id is None:
        # Si no se proporciona un file_id, obtenemos todos los archivos disponibles
        data_files = DataFile.objects.all()
        context = {
            'data_files': data_files
        }
        return render(request, 'home/index.html', context)
    else:
        # Si se proporciona un file_id, obtenemos los datos de ese archivo
        data_file = get_object_or_404(DataFile, id=file_id)
        records = DataRecord.objects.filter(file=data_file)

        initial_labels = []
        initial_values = []
        if records.exists() and data_file.columns:
            first_col = data_file.columns[0]
            second_col = data_file.columns[1] if len(data_file.columns) > 1 else data_file.columns[0]

            for record in records:
                initial_labels.append(str(record.data.get(first_col, '')))
                try:
                    initial_values.append(float(record.data.get(second_col, 0)))
                except (ValueError, TypeError):
                    initial_values.append(0)

        context = {
            'file': data_file,
            'columns': data_file.columns,
            'initial_labels': initial_labels,
            'initial_values': initial_values
        }

        return render(request, 'home/index.html', context)

def data_history(request):
    return render(request, 'home/data_history.html')

def reports(request):
    return render(request, 'home/reports.html')

def settings(request):
    return render(request, 'home/settings.html')

def data_management(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        try:
            file = request.FILES['csv_file']
            # Leer el CSV con pandas
            df = pd.read_csv(file)
            
            # Crear registro del archivo
            data_file = DataFile.objects.create(
                name=file.name,
                file=file,
                description=request.POST.get('description', ''),
                columns=list(df.columns),
                row_count=len(df)
            )
            
            # Guardar cada fila como un registro
            records = [
                DataRecord(
                    file=data_file,
                    data=row.to_dict()
                )
                for _, row in df.iterrows()
            ]
            DataRecord.objects.bulk_create(records)
            
            messages.success(request, 'Archivo cargado exitosamente')
            return redirect('data-preview', file_id=data_file.id)
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
    
    # Obtener lista de archivos cargados
    files = DataFile.objects.all().order_by('-uploaded_at')
    return render(request, 'home/data_management.html', {'files': files})


def data_preview(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id)
    records = DataRecord.objects.filter(file=data_file)[:100]
    all_columns = data_file.columns
    
    # Obtener columnas visibles de la sesión o usar todas por defecto
    visible_columns = request.session.get(f'visible_columns_{file_id}', all_columns)
    
    if request.method == 'POST':
        # Actualizar columnas visibles
        visible_columns = request.POST.getlist('columns')
        request.session[f'visible_columns_{file_id}'] = visible_columns
        return JsonResponse({'success': True})
    
    context = {
        'file': data_file,
        'records': records,
        'all_columns': all_columns,
        'visible_columns': visible_columns
    }
    return render(request, 'home/data_preview.html', context)

def delete_file(request, file_id):
    if request.method == 'POST':
        data_file = get_object_or_404(DataFile, id=file_id)
        data_file.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def data_visualization(request, file_id=None):
    if file_id is None:
        return redirect('data-selection')
    
    data_file = get_object_or_404(DataFile, id=file_id)
    records = DataRecord.objects.filter(file=data_file)
    
    if request.method == 'POST':
        x_axis = request.POST.get('x_axis')
        y_axis = request.POST.get('y_axis')
        chart_type = request.POST.get('chart_type', 'line')
        chart_title = request.POST.get('chart_title', '')
        chart_subtitle = request.POST.get('chart_subtitle', '')
        show_legend = request.POST.get('show_legend', 'true') == 'true'
        
        labels = []
        values = []
        for record in records:
            labels.append(str(record.data.get(x_axis, '')))
            try:
                values.append(float(record.data.get(y_axis, 0)))
            except (ValueError, TypeError):
                values.append(0)
        
        return JsonResponse({
            'success': True,
            'labels': labels,
            'values': values,
            'chart_type': chart_type,
            'chart_title': chart_title,
            'chart_subtitle': chart_subtitle,
            'show_legend': show_legend
        })
    
    initial_labels = []
    initial_values = []
    if records.exists() and data_file.columns:
        first_col = data_file.columns[0]
        second_col = data_file.columns[1] if len(data_file.columns) > 1 else data_file.columns[0]
        
        for record in records:
            initial_labels.append(str(record.data.get(first_col, '')))
            try:
                initial_values.append(float(record.data.get(second_col, 0)))
            except (ValueError, TypeError):
                initial_values.append(0)
    
    context = {
        'file': data_file,
        'columns': data_file.columns,
        'initial_labels': initial_labels,
        'initial_values': initial_values,
        'chart_types': [
            {'value': 'line', 'label': 'Líneas'},
            {'value': 'bar', 'label': 'Barras'},
            {'value': 'pie', 'label': 'Circular'},
            {'value': 'doughnut', 'label': 'Dona'},
            {'value': 'polarArea', 'label': 'Área Polar'},
            {'value': 'radar', 'label': 'Radar'}
        ]
    }
    return render(request, 'home/data_visualization.html', context)
from django.shortcuts import render
from django.http import JsonResponse
from .models import DataFile, DataRecord
import pandas as pd


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import pandas as pd
from .models import DataFile



from django.http import JsonResponse
import pandas as pd
from .models import DataFile


from django.shortcuts import render, redirect
from .models import DataFile

from django.shortcuts import redirect

from django.shortcuts import render, redirect
from .models import DataFile

def data_selection(request):
    # Obtener todos los archivos de datos
    data_files = DataFile.objects.all()

    if request.method == 'POST':
        # Obtener el file_id del formulario
        file_id = request.POST.get('file_id')
        if file_id:
            # Redirigir al gráfico usando el file_id en la URL (sin parámetro extra)
            return redirect('data-visualization', file_id=file_id)  # Redirige con el file_id en la URL

    return render(request, 'home/data_selection.html', {'data_files': data_files})

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import DataFile, DataRecord
import pandas as pd
from django.contrib import messages


def data_management(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        try:
            file = request.FILES['csv_file']
            
            # Verificar que sea un archivo CSV
            if not file.name.endswith('.csv'):
                messages.error(request, 'Por favor, sube un archivo CSV válido')
                return redirect('data-management')
            
            # Leer el CSV con pandas
            df = pd.read_csv(file)
            
            # Crear registro del archivo
            data_file = DataFile.objects.create(
                name=file.name,
                file=file,
                description=request.POST.get('description', ''),
                columns=list(df.columns),
                visible_columns=list(df.columns),  # Inicialmente todas las columnas son visibles
                row_count=len(df)
            )
            
            # Crear registros en lotes
            batch_size = 1000
            records = []
            for _, row in df.iterrows():
                records.append(
                    DataRecord(
                        file=data_file,
                        data=row.to_dict()
                    )
                )
                if len(records) >= batch_size:
                    DataRecord.objects.bulk_create(records)
                    records = []
            
            if records:  # Crear cualquier registro restante
                DataRecord.objects.bulk_create(records)
            
            messages.success(request, 'Archivo cargado exitosamente')
            return redirect('data-preview', file_id=data_file.id)
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return redirect('data-management')
    
    files = DataFile.objects.all().order_by('-is_favorite', '-uploaded_at')
    return render(request, 'home/data_management.html', {'files': files})

def file_exists(file_id):
    try:
        file = DataFile.objects.get(id=file_id)
        return os.path.exists(file.file.path)
    except (DataFile.DoesNotExist, ValueError):
        return False

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import DataFile, DataRecord
import pandas as pd
from django.contrib import messages


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import DataFile

@require_POST
def toggle_favorite(request, file_id):
    print(f"DEBUG: Recibida solicitud para file_id: {file_id}")
    
    try:
        # Primero intentamos encontrar el archivo en DataFile
        try:
            file = DataFile.objects.get(id=file_id)
            print(f"DEBUG: Archivo encontrado en DataFile: {file.name}")
            
            # Quitar favorito de todos los archivos DataFile
            DataFile.objects.exclude(id=file_id).update(is_favorite=False)
            
            # Toggle el favorito del archivo actual
            file.is_favorite = not file.is_favorite
            file.save()
            
        except DataFile.DoesNotExist:
            print(f"DEBUG: Archivo no encontrado en DataFile, buscando en File")
            file = DataFile.objects.get(id=file_id)
            
            # Quitar favorito de todos los archivos File
            DataFile.objects.exclude(id=file_id).update(is_favorite=False)
            
            # Toggle el favorito del archivo actual
            file.is_favorite = not file.is_favorite
            file.save()

        print(f"DEBUG: Estado final de is_favorite: {file.is_favorite}")
        
        return JsonResponse({
            'success': True,
            'is_favorite': file.is_favorite,
            'file_name': file.name
        })
        
    except Exception as e:
        print(f"DEBUG: Error en toggle_favorite: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
# Actualizar la vista de data_preview para incluir el estado de favorito
def data_preview(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id)
    records = DataRecord.objects.filter(file=data_file)[:100]
    all_columns = data_file.columns
    
    # Obtener columnas visibles de la sesión o usar todas por defecto
    visible_columns = request.session.get(f'visible_columns_{file_id}', all_columns)
    
    if request.method == 'POST':
        # Actualizar columnas visibles
        visible_columns = request.POST.getlist('columns')
        request.session[f'visible_columns_{file_id}'] = visible_columns
        return JsonResponse({'success': True})
    
    context = {
        'file': data_file,
        'records': records,
        'all_columns': all_columns,
        'visible_columns': visible_columns,
        'is_favorite': data_file.is_favorite
    }
    return render(request, 'home/data_preview.html', context)

# views.py
from django.http import JsonResponse
from .models import DataFile
import pandas as pd
from django.http import JsonResponse
from .models import DataFile
import pandas as pd
import os
from django.conf import settings
from django.http import JsonResponse
from .models import DataFile
import pandas as pd
import os
import traceback

def get_favorite_data(request):
    try:
        print("=== Iniciando get_favorite_data ===")
        all_files = list(DataFile.objects.all())
        favorite_file = next((file for file in all_files if file.is_favorite), None)
        
        if not favorite_file:
            return JsonResponse({'error': 'No se encontró archivo favorito'}, status=404)

        try:
            df = pd.read_csv(favorite_file.file.path)
            
            # Asegurarnos de que todas las columnas necesarias estén presentes
            required_columns = [
                'Nombre de la campaña',
                'Resultados',
                'Alcance',
                'Impresiones',
                'Clics en el enlace',
                'CPC (Coste por clic en el enlace)',
                'Seguidores o Me gusta',
                'Presupuesto de la campaña',
                'Importe gastado (HNL)',
                'CPM (coste por 1000 impresiones)'
            ]
            
            for col in required_columns:
                if col not in df.columns:
                    return JsonResponse({
                        'error': f'Columna requerida no encontrada: {col}',
                        'columnas_disponibles': df.columns.tolist()
                    }, status=400)
            
            # Convertir valores numéricos
            numeric_columns = [
                'Resultados', 'Alcance', 'Impresiones', 'Clics en el enlace',
                'CPC (Coste por clic en el enlace)', 'Seguidores o Me gusta',
                'Presupuesto de la campaña', 'Importe gastado (HNL)',
                'CPM (coste por 1000 impresiones)'
            ]
            
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Convertir a formato JSON
            result_data = df.to_dict('records')
            return JsonResponse(result_data, safe=False)

        except Exception as e:
            print(f"Error procesando CSV: {str(e)}")
            return JsonResponse({'error': f'Error procesando archivo: {str(e)}'}, status=500)

    except Exception as e:
        print(f"Error general: {str(e)}")
        return JsonResponse({'error': f'Error del servidor: {str(e)}'}, status=500)
def get_favorite_metric_data(request, metric_type):
    try:
        print(f"=== Obteniendo datos para métrica: {metric_type} ===")
        
        # Obtener el archivo favorito
        all_files = list(DataFile.objects.all())
        favorite_file = next((file for file in all_files if file.is_favorite), None)
        
        if not favorite_file:
            return JsonResponse({'error': 'No se encontró archivo favorito'}, status=404)
        
        # Mapear el tipo de métrica con el nombre de la columna
        metric_mapping = {
            'results': 'Resultados',
            'reach': 'Alcance',
            'impressions': 'Impresiones'
        }
        
        column = metric_mapping.get(metric_type)
        if not column:
            return JsonResponse({'error': 'Tipo de métrica no válido'}, status=400)
        
        try:
            df = pd.read_csv(favorite_file.file.path)
            
            # Verificar que las columnas existan
            if 'Nombre de la campaña' not in df.columns or column not in df.columns:
                return JsonResponse({
                    'error': 'Columnas requeridas no encontradas',
                    'columnas_disponibles': df.columns.tolist()
                }, status=400)
            
            # Seleccionar y preparar los datos
            data = df[['Nombre de la campaña', column]].copy()
            data[column] = pd.to_numeric(data[column], errors='coerce')
            data = data.dropna()
            
            # Convertir a lista de diccionarios
            result_data = data.to_dict('records')
            
            return JsonResponse(result_data, safe=False)
            
        except Exception as e:
            print("Error procesando el CSV:", str(e))
            return JsonResponse({
                'error': 'Error procesando el archivo CSV',
                'details': str(e)
            }, status=500)
            
    except Exception as e:
        print("Error general:", str(e))
        return JsonResponse({
            'error': 'Error interno del servidor',
            'details': str(e)
        }, status=500)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import DataFile, DataRecord


@require_http_methods(["POST"])
def save_data_changes(request, file_id):
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        
        file = get_object_or_404(DataFile, id=file_id)
        
        # Actualizar registros en la base de datos
        for change in changes:
            record = DataRecord.objects.get(id=change['recordId'])
            record.data[change['column']] = change['value']
            record.save()
        
        # Actualizar el archivo CSV
        df = pd.read_csv(file.file.path)
        for change in changes:
            record = DataRecord.objects.get(id=change['recordId'])
            row_index = int(record.id)  # o la lógica que uses para mapear registros a filas
            df.at[row_index, change['column']] = change['value']
        
        df.to_csv(file.file.path, index=False)
        
        # Limpiar la caché
        cache_key = f'file_records_{file.id}'
        cache.delete(cache_key)
        
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error en save_data_changes: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
def clear_file_cache(file_id):
    cache_keys = [
        f'file_records_{file_id}',
        f'file_data_{file_id}',
        f'file_columns_{file_id}'
    ]
    for key in cache_keys:
        cache.delete(key)

@require_http_methods(["POST"])
def delete_rows(request, file_id):
    try:
        data = json.loads(request.body)
        record_ids = data.get('recordIds', [])
        
        file = get_object_or_404(DataFile, id=file_id)
        
        with transaction.atomic():  # Usar transacción para asegurar consistencia
            # Obtener los índices antes de borrar
            records_to_delete = DataRecord.objects.filter(
                id__in=record_ids, 
                file=file
            )
            
            # Borrar los registros
            deleted_count = records_to_delete.count()
            records_to_delete.delete()
            
            # Actualizar el conteo en el modelo
            file.row_count = DataRecord.objects.filter(file=file).count()
            file.save()
            
            try:
                # Actualizar el archivo CSV
                df = pd.read_csv(file.file.path)
                df = df.drop(df.index[records_to_delete])
                df.reset_index(drop=True, inplace=True)
                df.to_csv(file.file.path, index=False)
            except Exception as csv_error:
                print(f"Error actualizando CSV: {csv_error}")
                # Aún si hay error con el CSV, continuamos con la respuesta
            
            # Limpiar caché
            cache.delete(f'file_records_{file.id}')
            
            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'new_total': file.row_count
            })
            
    except Exception as e:
        print(f"Error en delete_rows: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .models import DataFile, DataRecord

@require_http_methods(["POST"])
def update_columns(request, file_id):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            selected_columns = data.get('columns', [])
        else:
            selected_columns = request.POST.getlist('columns')

        if not selected_columns:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar al menos una columna'
            }, status=400)

        file = get_object_or_404(DataFile, id=file_id)
        
        with transaction.atomic():
            # Actualizar el modelo
            file.visible_columns = selected_columns
            file.save()
            
            try:
                # Actualizar el CSV
                df = pd.read_csv(file.file.path)
                all_columns = list(df.columns)
                
                # Verificar que todas las columnas seleccionadas existen
                if not all(col in all_columns for col in selected_columns):
                    raise ValueError("Algunas columnas seleccionadas no existen en el archivo")
                
                # Reordenar columnas manteniendo todas pero marcando visibilidad
                df = df[selected_columns + [col for col in all_columns if col not in selected_columns]]
                df.to_csv(file.file.path, index=False)
                
            except Exception as csv_error:
                print(f"Error actualizando CSV: {csv_error}")
                # Continuamos incluso si hay error con el CSV
            
            # Limpiar caché
            cache.delete(f'file_records_{file.id}')
            
            return JsonResponse({'success': True})
            
    except Exception as e:
        print(f"Error en update_columns: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
# templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

# También necesitamos actualizar edit_data para manejar correctamente los campos JSON
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.template.exceptions import TemplateDoesNotExist
import json
from .models import DataFile, DataRecord

@require_http_methods(["GET"])
def edit_data(request, file_id):
    try:
        file = get_object_or_404(DataFile, id=file_id)
        records = DataRecord.objects.filter(file=file)
        
        # Obtener las columnas
        try:
            all_columns = list(file.columns) if file.columns else []
            visible_columns = list(file.visible_columns) if file.visible_columns else all_columns
        except (TypeError, json.JSONDecodeError):
            visible_columns = all_columns = []

        context = {
            'file': file,
            'records': records,
            'visible_columns': visible_columns,
            'all_columns': all_columns,
        }
        
        # Intentar con diferentes ubicaciones de template
        templates_to_try = [
            'edit_data.html',
            'home/edit_data.html',
        ]
        
        for template_name in templates_to_try:
            try:
                return render(request, template_name, context)
            except TemplateDoesNotExist:
                continue
        
        # Si ningún template funciona, lanzar error
        raise TemplateDoesNotExist("No se encontró el template edit_data.html")
        
    except TemplateDoesNotExist as e:
        print(f"Error: No se encontró el template - {str(e)}")
        return JsonResponse({
            'error': 'No se encontró el template. Verifica la ubicación del archivo edit_data.html'
        }, status=500)
    except Exception as e:
        print(f"Error en edit_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
import pandas as pd

def update_file_data(file, changes):
    """
    Actualiza los datos del archivo con los cambios proporcionados
    """
    # Cargar el CSV actual
    df = pd.read_csv(file.file.path)
    
    # Aplicar los cambios
    for change in changes:
        row_id = int(change['rowId'])
        column = change['column']
        value = change['value']
        
        # Actualizar el valor en el DataFrame
        df.at[row_id, column] = value
    
    # Guardar los cambios
    df.to_csv(file.file.path, index=False)

def delete_file_rows(file, row_ids):
    """
    Elimina las filas especificadas del archivo
    """
    # Cargar el CSV actual
    df = pd.read_csv(file.file.path)
    
    # Convertir row_ids a enteros
    row_ids = [int(id) for id in row_ids]
    
    # Eliminar las filas
    df = df.drop(row_ids)
    
    # Resetear los índices
    df = df.reset_index(drop=True)
    
    # Guardar los cambios
    df.to_csv(file.file.path, index=False)

def update_visible_columns(file, columns):
    """
    Actualiza las columnas visibles del archivo
    """
    # Cargar el CSV actual
    df = pd.read_csv(file.file.path)
    
    # Filtrar solo las columnas seleccionadas
    df = df[columns]
    
    # Guardar los cambios
    df.to_csv(file.file.path, index=False)
    
    # Actualizar la configuración de columnas visibles en tu modelo
    file.visible_columns = columns
    file.save()

import pandas as pd
import json
from django.core.cache import cache

# templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

def get_file_records(file):
    """
    Lee los registros del archivo CSV y los devuelve en formato adecuado para la vista
    """
    try:
        # Intentar leer desde la cache primero
        cache_key = f'file_records_{file.id}'
        records = cache.get(cache_key)
        
        if records is None:
            # Leer el archivo CSV
            df = pd.read_csv(file.file.path)
            
            # Convertir el DataFrame a una lista de diccionarios
            records = []
            for index, row in df.iterrows():
                records.append({
                    'id': index,
                    'data': row.to_dict()
                })
            
            # Guardar en cache por 5 minutos
            cache.set(cache_key, records, 300)
        
        return records
    except Exception as e:
        print(f"Error al leer el archivo: {str(e)}")
        return []

def get_visible_columns(file):
    """
    Obtiene las columnas visibles para el archivo
    """
    try:
        # Si tienes un campo en tu modelo File para almacenar las columnas visibles
        if hasattr(file, 'visible_columns') and file.visible_columns:
            return json.loads(file.visible_columns)
        
        # Si no hay columnas visibles definidas, obtener todas las columnas
        df = pd.read_csv(file.file.path)
        return list(df.columns)
    except Exception as e:
        print(f"Error al obtener columnas visibles: {str(e)}")
        return []

def get_all_columns(file):
    """
    Obtiene todas las columnas disponibles en el archivo
    """
    try:
        df = pd.read_csv(file.file.path)
        return list(df.columns)
    except Exception as e:
        print(f"Error al obtener todas las columnas: {str(e)}")
        return []