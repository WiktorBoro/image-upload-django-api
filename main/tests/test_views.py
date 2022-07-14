from rest_framework import status
from .test_setup import TestSetUp


class TestGetImageList(TestSetUp):

    def test_should_return_images_list(self):
        test_user = 'Mike'

        response = self.client.get('/api/get-image-list?user_name={}'.format(test_user))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertNotEqual(list(response.data.keys())[0], 'Failure')
        self.assertEqual(type(list(response.data.values())[0]), dict)

    def test_should_return_error_response_when_user_dont_have_image(self):
        test_user = 'John'

        response = self.client.get('/api/get-image-list?user_name={}'.format(test_user))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data.keys())[0], 'Failure')
        self.assertEqual(type(list(response.data.values())[0]), str)

    def test_should_return_error_response(self):
        response = self.client.get('/api/get-image-list')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(response.data.keys())[0], 'Failure')
        self.assertEqual(type(list(response.data.values())[0]), str)


class TestUploadImage(TestSetUp):

    def test_should_return_links_for_enterprise_accout_tier(self):
        test_user = 'Janna'

        response = self.client.post('/api/upload-image?user_name={}'.format(test_user), self.body_upload_image)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Upload'], 'Success')
        self.assertEqual(type(response.data['links']), dict)
        self.assertIn('400', response.data['links'])
        self.assertIn('200', response.data['links'])
        self.assertIn('original', response.data['links'])

    def test_should_return_links_for_basic_accout_tier(self):
        test_user = 'Mike'

        response = self.client.post('/api/upload-image?user_name={}'.format(test_user), self.body_upload_image)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Upload'], 'Success')
        self.assertEqual(type(response.data['links']), dict)
        self.assertNotIn('400', response.data['links'])
        self.assertIn('200', response.data['links'])
        self.assertNotIn('original', response.data['links'])


class TestGenerateExpiringLink(TestSetUp):

    def test_should_return_expiring_links_for_enterprise_tier(self):
        test_user = 'Janna'

        response = self.client.post('/api/generate-expiring-link?user_name={}'.format(test_user),
                                    self.body_expiring_link)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['Generating'], 'Success')
        self.assertEqual(type(response.data['expiring_link']), str)
        self.assertIn('expiring_link', response.data)

    def test_should_return_error_for_basic_tier(self):
        test_user = 'Mike'

        response = self.client.post('/api/generate-expiring-link?user_name={}'.format(test_user),
                                    self.body_expiring_link)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Failure', response.data)
        self.assertEqual(response.data['Failure'], 'You do not have the correct account tier, buy an upgrade!')
