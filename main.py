import os, requests,datetime
from os.path import basename, dirname
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


class Cloner:
	def __init__(self, url, project_dir = None, completed = []) -> None:
		super().__init__()
		print(f"Waktu dimulai : {datetime.datetime.now()}")
		self.request = requests.Session()
		self.url = url
		self.urlparsed = urlparse(url)
		self.project_dir = os.path.abspath(os.path.realpath(project_dir if project_dir else self.urlparsed.netloc))
		
		resp = self.request.get(url)
		self.bs4 = BeautifulSoup(resp.text, 'lxml')

		self.__resolveLink(['a', 'area', 'base', 'link'],'href', self.__resolveBaseurl())
		self.__resolveLink(['audio', 'embed', 'iframe', 'img', 'input', 'script', 'source', 'track', 'video'],'src', self.__resolveBaseurl())

		self.pages = []
		self.__completed = completed
		self.startQueue()

	def __resolveBaseurl(self):
		baseTag = self.bs4.select_one('head > base')

		path = f"{self.urlparsed.scheme if self.urlparsed.scheme != '' else 'http' }://{self.urlparsed.netloc}"
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

	def __resolveLink(self, elements, mode, baseurl = ''):
		for el in self.bs4.find_all(elements):
			link = el.get(mode)
			if link and link != '#':
				urlparsed = urlparse(link)
				if not urlparsed.fragment:
					if urlparsed.netloc:
						if urlparsed.netloc == self.urlparsed.netloc:
							link = urljoin(baseurl, self.__resolveUrlPath(urlparsed).lstrip('/'))
						else:
							if not urlparsed.scheme:
								link = f"{urlparsed.scheme if urlparsed.scheme != '' else 'http' }://{urlparsed.netloc}/{self.__resolveUrlPath(urlparsed)}"
					else:
						link = urljoin(baseurl, link)

				el.attrs[mode] = link

	def downloadAsset(self, elements, attribute):
		for el in self.bs4.find_all(elements):
			link = el.get(attribute)
			linkparse = urlparse(link)
			if linkparse.path and linkparse.netloc == self.urlparsed.netloc and link not in self.__completed:
				path = os.path.join(self.project_dir, linkparse.path.lstrip('/'))
				dirname = os.path.dirname(path)
				basename = os.path.basename(path)
				if basename:
					os.makedirs(dirname, exist_ok=True)

					resp = self.request.get(link)
					with open(path, 'wb') as file:
						file.write(resp.content if resp.status_code == 200 else str.encode(''))
						self.__completed.append(link)

	def downloadPage(self):
		path = os.path.join(self.project_dir, self.urlparsed.path.lstrip('/') if self.urlparsed.path.lstrip('/') else 'index.html')
		self.__resolveLink(['a', 'area', 'base', 'link'],'href')
		self.__resolveLink(['audio', 'embed', 'iframe', 'img', 'input', 'script', 'source', 'track', 'video'],'src')
		
		with open(path, 'w') as file:
			file.write(self.bs4.prettify())

		self.__resolveLink(['a', 'area', 'base', 'link'],'href', self.__resolveBaseurl())
		self.__resolveLink(['audio', 'embed', 'iframe', 'img', 'input', 'script', 'source', 'track', 'video'],'src', self.__resolveBaseurl())

	def startQueue(self):
		self.downloadAsset(['audio', 'embed', 'iframe', 'img', 'input', 'script', 'source', 'track', 'video'], 'src')
		self.downloadAsset(['area', 'link'], 'href')
		self.downloadPage()

		for a in self.bs4.select('a'):
			url = a.get('href')
			if url and url != '#' and url not in self.__completed:
				urlparsed = urlparse(url)
				if urlparsed.netloc == self.urlparsed.netloc:
					print(url)
					self.__completed.append(url)
					Cloner(url, completed=self.__completed)

if __name__ == "__main__":
	# url = "https://demo.adminkit.io/"
	url = "https://siplah.tubankab.go.id/"
	cloner = Cloner(url)