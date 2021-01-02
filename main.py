import os, requests, re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


class Cloner:
	def __init__(self, url, project_dir = None, completed = []) -> None:
		super().__init__()
		self.request = requests.Session()
		self.url = url
		self.urlparsed = urlparse(url)
		self.project_dir = os.path.abspath(os.path.realpath(project_dir if project_dir else self.urlparsed.netloc))
		
		resp = self.request.get(url)
		self.pages = []
		self.__completed = completed
		if resp.status_code == 200:
			self.bs4 = BeautifulSoup(resp.text, 'lxml')

			self.startQueue()
		else:
			self.__completed.append(url)
			print(f"{url} 404 Not Found.")

	def __resolveBaseurl(self):
		baseTag = self.bs4.select_one('head > base')

		path = os.path.dirname(urljoin(self.url,'.'))
		if baseTag:
			href = baseTag.get('href')
			urlparsed = urlparse(href)
			if not urlparsed.netloc:
				path = os.path.join(f"{self.urlparsed.scheme if self.urlparsed.scheme != '' else 'http' }://{self.urlparsed.netloc}", self.__resolveUrlPath(urlparsed.path))
			else:
				path = href.strip('/')
			baseTag.decompose()

		return path

	def __resolveUrlPath(self, urlparsed):
		path = urlparsed.path if urlparsed.path else ''
		params = ';' + urlparsed.params if urlparsed.params else ''
		query = '?' + urlparsed.query if urlparsed.query else ''
		fragment = '#' + urlparsed.fragment if urlparsed.fragment else ''

		return os.path.abspath(f"{path}{params}{query}{fragment}")


	def __resolveCssUrl(self, pathfile, linkRaw):
		with open(pathfile, 'rb') as file:
			content = file.read().decode('utf-8')
			links = re.findall(r'url\((.*?)\)', content)
			for link in links:
				link = link.strip('\'').strip('"')

				linkParsed = urlparse(link)
				link = urljoin(linkRaw, link)
				link = urljoin(link, linkParsed.path)
				linkParsed = urlparse(link)
				
				if linkParsed.netloc == self.urlparsed.netloc and link not in self.__completed:
	
					path = os.path.join(self.project_dir, linkParsed.path.lstrip('/'))
					dirname = os.path.dirname(path)
					basename = os.path.basename(path)

					if basename:
						os.makedirs(dirname, exist_ok=True)

						print(link,"DOWNLOADING...")

						resp = self.request.get(link)
						with open(path, 'wb') as file:
							file.write(resp.content if resp.status_code == 200 else str.encode(''))
							self.__completed.append(link)
							print(link,"DONE...")


	def downloadAsset(self, elements, attribute):
		for el in self.bs4.find_all(elements):
			link = el.get(attribute)
			if link and not str(link).startswith('javascript:void') and not str(link).startswith('data:'):
				linkparse = urlparse(link)
				

				if not linkparse.netloc or linkparse.netloc == self.urlparsed.netloc:

					link = urljoin(self.__resolveBaseurl()+'/', linkparse.path.lstrip('/'))

					linkparse = urlparse(link)
					
					if linkparse.netloc == self.urlparsed.netloc and link not in self.__completed:
						path = os.path.join(self.project_dir, linkparse.path.lstrip('/'))
						dirname = os.path.dirname(path)
						basename = os.path.basename(path)
						
						if basename and basename != '.':
							os.makedirs(dirname, exist_ok=True)

							print(link,"DOWNLOADING...")

							resp = self.request.get(link)
							with open(path, 'wb') as file:
								file.write(resp.content if resp.status_code == 200 else str.encode(''))
								print(link,"DONE...")

							if basename.endswith('.css'):
								self.__resolveCssUrl(path, link)

			self.__completed.append(link)


	def downloadPage(self):
		if self.url not in self.__completed:
			path = os.path.join(self.project_dir, self.urlparsed.path.lstrip('/') if self.urlparsed.path.lstrip('/') else 'index.html')
			dirname = os.path.dirname(path)
			basename = os.path.basename(path)
			if basename:
				os.makedirs(dirname, exist_ok=True)

				with open(path, 'w') as file:
					file.write(self.bs4.prettify())
					self.__completed.append(self.url)
					
					print(self.url, "DONE...")
					

	def startQueue(self):
		self.downloadPage()
		self.downloadAsset(['audio', 'embed', 'iframe', 'img', 'input', 'script', 'source', 'track', 'video'], 'src')
		self.downloadAsset(['area', 'link'], 'href')

		for a in self.bs4.select('a'):
			url = a.get('href')
			if url and '#' not in url:
				urlparsed = urlparse(url)
				if not urlparsed.netloc or urlparsed.netloc == self.urlparsed.netloc:
					url = urljoin(self.__resolveBaseurl()+'/', urlparsed.path.lstrip('/'))
					if url not in self.__completed:
						Cloner(url, project_dir=self.project_dir, completed=self.__completed)

if __name__ == "__main__":
	url = "https://demo.adminkit.io"
	# url = "https://demos.creative-tim.com/argon-dashboard-pro/pages/dashboards/dashboard.html"
	cloner = Cloner(url)