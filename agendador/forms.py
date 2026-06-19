from pathlib import Path
from django import forms
from django.conf import settings
from .models import TarefaAgendada


def _pasta_choices():
    scripts_dir = settings.BASE_DIR / 'scripts'
    if not scripts_dir.exists():
        return [('', '— Selecione a pasta —')]
    pastas = sorted(p.name for p in scripts_dir.iterdir() if p.is_dir() and not p.name.startswith('.'))
    return [('', '— Selecione a pasta —')] + [(p, p) for p in pastas]


class TarefaAgendadaForm(forms.ModelForm):

    pasta_script = forms.ChoiceField(
        choices=_pasta_choices,
        label='Pasta',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'style': 'max-width:280px;', 'required': 'required'}),
    )
    nome_script = forms.CharField(
        label='Nome do script',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ex: meu_script.py',
            'style': 'max-width:320px;',
        }),
    )

    class Meta:
        model = TarefaAgendada
        fields = ['nome', 'descricao', 'modulo', 'ativa', 'assunto', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'modulo': forms.Select(attrs={'class': 'form-select', 'style': 'max-width:260px;'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assunto opcional...'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações opcionais...'}),
        }

    def clean_pasta_script(self):
        pasta = self.cleaned_data.get('pasta_script', '').strip()
        if not pasta:
            raise forms.ValidationError('Selecione uma pasta.')
        return pasta

    def clean(self):
        cleaned = super().clean()
        pasta = cleaned.get('pasta_script', '').strip()
        nome = cleaned.get('nome_script', '').strip()

        if not nome:
            self.add_error('nome_script', 'Informe o nome do script.')
            return cleaned

        if not nome.endswith('.py'):
            nome += '.py'
            cleaned['nome_script'] = nome

        caminho = Path('scripts') / pasta / nome
        cleaned['caminho_script'] = str(caminho)
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.caminho_script = self.cleaned_data.get('caminho_script', '')
        if commit:
            instance.save()
        return instance
