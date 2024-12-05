from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import pandas as pd
import json

class DataFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='csv_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    columns = models.JSONField(default=list)  # Añadir default
    visible_columns = models.JSONField(null=True, blank=True)  # Añadir blank=True
    row_count = models.IntegerField(default=0)
    is_favorite = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Primero guardar el archivo
        super().save(*args, **kwargs)
        
        # Procesar el archivo solo si es nuevo
        if is_new and self.file:
            try:
                df = pd.read_csv(self.file.path)
                self.row_count = len(df)
                self.columns = list(df.columns)
                self.visible_columns = list(df.columns)
                
                # Guardar los cambios en el modelo
                super().save(*args, **kwargs)
                
                # Crear registros de datos
                records = []
                for _, row in df.iterrows():
                    records.append(DataRecord(
                        file=self,
                        data=row.to_dict()
                    ))
                
                # Crear los registros en lotes
                DataRecord.objects.bulk_create(records)
            except Exception as e:
                print(f"Error al procesar el archivo: {str(e)}")
                # Podrías querer hacer algo más aquí, como eliminar el archivo
                raise e

    def __str__(self):
        return f"{self.name} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

    def get_visible_columns(self):
        """Método auxiliar para obtener columnas visibles"""
        return self.visible_columns or self.columns

    def update_visible_columns(self, columns):
        """Método auxiliar para actualizar columnas visibles"""
        self.visible_columns = columns
        self.save()

class DataRecord(models.Model):
    file = models.ForeignKey(DataFile, on_delete=models.CASCADE, related_name='records')
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['file', 'created_at'])
        ]
        ordering = ['created_at']  # Añadir ordenamiento por defecto

    def get_value(self, column):
        """Obtener valor de una columna de forma segura"""
        return self.data.get(column, '')

    def update_value(self, column, value):
        """Actualizar valor de una columna"""
        self.data[column] = value
        self.save()

    def __str__(self):
        return f"Record for {self.file.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"