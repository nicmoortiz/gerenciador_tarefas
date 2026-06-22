from django.test import TestCase
from django.urls import reverse


class PaineisViewsTests(TestCase):
    def test_lista_paineis_renderiza_visao_inicial(self):
        response = self.client.get(reverse('lista_paineis'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Painéis')
        self.assertContains(response, 'Caminho Tableau')
