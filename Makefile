.PHONY: lint test package package-desktop-release eval

lint:
	pnpm lint

test:
	pnpm test

package:
	pnpm package

package-desktop-release:
	pnpm package:desktop-release

eval:
	pnpm eval
