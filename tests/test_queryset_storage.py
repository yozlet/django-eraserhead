try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from django.test import TestCase

from eraserhead.queryset_storage import QuerySetStorage


class QuerySetStorageTestCase(TestCase):

    def test_add_wrapped_model_instance(self):
        """ Should increase instances count after add new model instance """
        qs_storage = QuerySetStorage(Mock(), Mock())
        self.assertEqual(qs_storage.instances_count, 0)
        qs_storage.add_wrapped_model_instance(Mock())
        self.assertEqual(qs_storage.instances_count, 1)

    def test_get_model_name(self):
        """ Should return correct queryset model name """
        queryset_mock = Mock()
        meta_mock = Mock()
        meta_mock.object_name = 'MyModel'
        model_mock = Mock()
        model_mock._meta = meta_mock
        queryset_mock.model = Mock(
            return_value=model_mock)
        qs_storage = QuerySetStorage(queryset_mock, Mock())
        self.assertEqual(qs_storage.model_name, 'MyModel')

    def test_get_queryset_id(self):
        """ Should return wrapped queryset object id """
        queryset_mock = Mock()
        qs_storage = QuerySetStorage(queryset_mock, Mock())
        self.assertEqual(qs_storage.queryset_id, id(queryset_mock))

    def test_total_used_fields(self):
        """ Should return all fields which were used at least once """
        queryset_mock = Mock()
        qs_storage = QuerySetStorage(queryset_mock, Mock())
        wrapped_instance1 = Mock()
        wrapped_instance1.eraserhead_used_fields = {'field1', 'field2'}
        wrapped_instance2 = Mock()
        wrapped_instance2.eraserhead_used_fields = {'field2', 'field3'}
        qs_storage.add_wrapped_model_instance(wrapped_instance1)
        qs_storage.add_wrapped_model_instance(wrapped_instance2)
        self.assertEqual(qs_storage.total_used_fields, {'field1', 'field2', 'field3'})

    def test_total_unused_fields(self):
        """ Should return all fields which weren't used at all """
        queryset_mock = Mock()
        qs_storage = QuerySetStorage(queryset_mock, Mock())
        wrapped_instance1 = Mock()
        wrapped_instance1.eraserhead_unused_fields = {'field1', 'field2', 'field3'}
        wrapped_instance2 = Mock()
        wrapped_instance2.eraserhead_unused_fields = {'field2', 'field3'}
        qs_storage.add_wrapped_model_instance(wrapped_instance1)
        qs_storage.add_wrapped_model_instance(wrapped_instance2)
        self.assertEqual(qs_storage.total_unused_fields, {'field2', 'field3'})

    def test_total_wasted_memory(self):
        """ Should return total wasted memory of all instances """
        queryset_mock = Mock()
        qs_storage = QuerySetStorage(queryset_mock, Mock())
        wrapped_instance1 = Mock()
        wrapped_instance1.eraserhead_unused_fields_size = 100
        wrapped_instance2 = Mock()
        wrapped_instance2.eraserhead_unused_fields_size = 144
        qs_storage.add_wrapped_model_instance(wrapped_instance1)
        qs_storage.add_wrapped_model_instance(wrapped_instance2)
        self.assertEqual(qs_storage.total_wasted_memory, 244)


class QuerySetStorageRecommendationsTestCase(TestCase):

    def setUp(self):
        super(QuerySetStorageRecommendationsTestCase, self).setUp()
        self.queryset_storage = QuerySetStorage(Mock(), Mock())

    def test_recommendations_all_good(self):
        """ Should return corresponding message if all fields are good """
        used_fields = ['foo', 'bar']
        unused_fields = []
        recommendation = self.queryset_storage.get_defer_recommendations(used_fields, unused_fields)
        self.assertTrue(recommendation.startswith("Nothing to do here"))

    def test_recommendations_defer(self):
        """ Should return defer call example if there are more used fields """
        used_fields = ['foo', 'bar', 'Jake']
        unused_fields = ['spam', 'Finn']
        recommendation = self.queryset_storage.get_defer_recommendations(used_fields, unused_fields)
        self.assertEqual(recommendation, "Model.objects.defer('spam', 'Finn')")

    def test_recommendations_only(self):
        """ Should return only call example if there are more unused fields """
        used_fields = ['foo', 'bar']
        unused_fields = ['spam', 'Finn', 'Jake']
        recommendation = self.queryset_storage.get_defer_recommendations(used_fields, unused_fields)
        self.assertEqual(recommendation, "Model.objects.only('foo', 'bar')")

    def test_recommendations_no_fields_was_used(self):
        """ Should return corresponding message if no fields was used """
        used_fields = []
        unused_fields = ['spam', 'bar']
        recommendation = self.queryset_storage.get_defer_recommendations(used_fields, unused_fields)
        self.assertEqual(recommendation, "No fields were used. Consider to remove this request")
