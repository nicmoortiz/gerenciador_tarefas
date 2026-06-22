from django import forms
from .models import (
    Projeto, PastaDeTrabalho, RegistroDesenvolvimento, FonteDeDados, FiltroFonte,
    ImagemFonte, Planilha, ImagemPlanilha, Painel, ImagemPainel,
    Historia, ImagemHistoria,
)


class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PastaDeTrabalhoForm(forms.ModelForm):
    class Meta:
        model = PastaDeTrabalho
        fields = ['nome', 'local_tableau_server', 'modulo', 'modulo_outro', 'setor_solicitante', 'solicitante']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'local_tableau_server': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: http://tableau.empresa.com.br/views/...'}),
            'modulo': forms.Select(attrs={'class': 'form-select', 'id': 'id_modulo'}),
            'modulo_outro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descreva o módulo'}),
            'setor_solicitante': forms.TextInput(attrs={'class': 'form-control'}),
            'solicitante': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RegistroDesenvolvimentoForm(forms.ModelForm):
    class Meta:
        model = RegistroDesenvolvimento
        fields = ['nome', 'data']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class FonteDeDadosForm(forms.ModelForm):
    class Meta:
        model = FonteDeDados
        fields = ['nome', 'conexao', 'banco', 'tipo_conexao', 'relacao_conexoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'conexao': forms.TextInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_conexao': forms.RadioSelect(),
            'relacao_conexoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class FiltroFonteForm(forms.ModelForm):
    class Meta:
        model = FiltroFonte
        fields = ['nome', 'detalhes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'detalhes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ImagemFonteForm(forms.ModelForm):
    class Meta:
        model = ImagemFonte
        fields = ['legenda', 'imagem', 'ordem']
        widgets = {
            'legenda': forms.TextInput(attrs={'class': 'form-control'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class PlanilhaForm(forms.ModelForm):
    class Meta:
        model = Planilha
        fields = ['nome', 'descricao', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class ImagemPlanilhaForm(forms.ModelForm):
    class Meta:
        model = ImagemPlanilha
        fields = ['secao', 'legenda', 'imagem', 'ordem']
        widgets = {
            'secao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Tela Inicial'}),
            'legenda': forms.TextInput(attrs={'class': 'form-control'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class PainelForm(forms.ModelForm):
    class Meta:
        model = Painel
        fields = ['nome', 'descricao', 'regras', 'planilhas', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'regras': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'planilhas': forms.CheckboxSelectMultiple(),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, pasta=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pasta:
            self.fields['planilhas'].queryset = Planilha.objects.filter(pasta=pasta)


class ImagemPainelForm(forms.ModelForm):
    class Meta:
        model = ImagemPainel
        fields = ['secao', 'legenda', 'imagem', 'ordem']
        widgets = {
            'secao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Visão Geral'}),
            'legenda': forms.TextInput(attrs={'class': 'form-control'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class HistoriaForm(forms.ModelForm):
    class Meta:
        model = Historia
        fields = ['nome', 'descricao', 'ordem']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class ImagemHistoriaForm(forms.ModelForm):
    class Meta:
        model = ImagemHistoria
        fields = ['secao', 'legenda', 'imagem', 'ordem']
        widgets = {
            'secao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ponto 1'}),
            'legenda': forms.TextInput(attrs={'class': 'form-control'}),
            'imagem': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
