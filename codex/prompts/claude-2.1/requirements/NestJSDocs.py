NEST_JS_FIRST_STEPS = """

### First steps

In this set of articles, you'll learn the **core fundamentals** of Nest. To get familiar with the essential building blocks of Nest applications, we'll build a basic CRUD application with features that cover a lot of ground at an introductory level.

#### Language

We're in love with [TypeScript](https://www.typescriptlang.org/), but above all - we love [Node.js](https://nodejs.org/en/). That's why Nest is compatible with both TypeScript and **pure JavaScript**. Nest takes advantage of the latest language features, so to use it with vanilla JavaScript we need a [Babel](https://babeljs.io/) compiler.

We'll mostly use TypeScript in the examples we provide, but you can always **switch the code snippets** to vanilla JavaScript syntax (simply click to toggle the language button in the upper right hand corner of each snippet).

#### Prerequisites

Please make sure that [Node.js](https://nodejs.org) (version >= 16) is installed on your operating system.

#### Setup

Setting up a new project is quite simple with the [Nest CLI](/cli/overview). With [npm](https://www.npmjs.com/) installed, you can create a new Nest project with the following commands in your OS terminal:

```bash
npm i -g @nestjs/cli
nest new project-name
```

> info **Hint** To create a new project with TypeScript's [stricter](https://www.typescriptlang.org/tsconfig#strict) feature set, pass the `--strict` flag to the `nest new` command.

The `project-name` directory will be created, node modules and a few other boilerplate files will be installed, and a `src/` directory will be created and populated with several core files.

<div class="file-tree">
  <div class="item">src</div>
  <div class="children">
    <div class="item">app.controller.spec.ts</div>
    <div class="item">app.controller.ts</div>
    <div class="item">app.module.ts</div>
    <div class="item">app.service.ts</div>
    <div class="item">main.ts</div>
  </div>
</div>

Here's a brief overview of those core files:

|                          |                                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `app.controller.ts`      | A basic controller with a single route.                                                                             |
| `app.controller.spec.ts` | The unit tests for the controller.                                                                                  |
| `app.module.ts`          | The root module of the application.                                                                                 |
| `app.service.ts`         | A basic service with a single method.                                                                               |
| `main.ts`                | The entry file of the application which uses the core function `NestFactory` to create a Nest application instance. |

The `main.ts` includes an async function, which will **bootstrap** our application:

```typescript
@@filename(main)

import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(3000);
}
bootstrap();
@@switch
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(3000);
}
bootstrap();
```

To create a Nest application instance, we use the core `NestFactory` class. `NestFactory` exposes a few static methods that allow creating an application instance. The `create()` method returns an application object, which fulfills the `INestApplication` interface. This object provides a set of methods which are described in the coming chapters. In the `main.ts` example above, we simply start up our HTTP listener, which lets the application await inbound HTTP requests.

Note that a project scaffolded with the Nest CLI creates an initial project structure that encourages developers to follow the convention of keeping each module in its own dedicated directory.

> info **Hint** By default, if any error happens while creating the application your app will exit with the code `1`. If you want to make it throw an error instead disable the option `abortOnError` (e.g., `NestFactory.create(AppModule, {{ '{' }} abortOnError: false {{ '}' }})`).

<app-banner-courses></app-banner-courses>

#### Platform

Nest aims to be a platform-agnostic framework. Platform independence makes it possible to create reusable logical parts that developers can take advantage of across several different types of applications. Technically, Nest is able to work with any Node HTTP framework once an adapter is created. There are two HTTP platforms supported out-of-the-box: [express](https://expressjs.com/) and [fastify](https://www.fastify.io). You can choose the one that best suits your needs.

|                    |                                                                                                                                                                                                                                                                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `platform-express` | [Express](https://expressjs.com/) is a well-known minimalist web framework for node. It's a battle tested, production-ready library with lots of resources implemented by the community. The `@nestjs/platform-express` package is used by default. Many users are well served with Express, and need take no action to enable it. |
| `platform-fastify` | [Fastify](https://www.fastify.io/) is a high performance and low overhead framework highly focused on providing maximum efficiency and speed. Read how to use it [here](/techniques/performance).                                                                                                                                  |

Whichever platform is used, it exposes its own application interface. These are seen respectively as `NestExpressApplication` and `NestFastifyApplication`.

When you pass a type to the `NestFactory.create()` method, as in the example below, the `app` object will have methods available exclusively for that specific platform. Note, however, you don't **need** to specify a type **unless** you actually want to access the underlying platform API.

```typescript
const app = await NestFactory.create<NestExpressApplication>(AppModule);
```

#### Running the application

Once the installation process is complete, you can run the following command at your OS command prompt to start the application listening for inbound HTTP requests:

```bash
npm run start
```

> info **Hint** To speed up the development process (x20 times faster builds), you can use the [SWC builder](/recipes/swc) by passing the `-b swc` flag to the `start` script, as follows `npm run start -- -b swc`.

This command starts the app with the HTTP server listening on the port defined in the `src/main.ts` file. Once the application is running, open your browser and navigate to `http://localhost:3000/`. You should see the `Hello World!` message.

To watch for changes in your files, you can run the following command to start the application:

```bash
npm run start:dev
```

This command will watch your files, automatically recompiling and reloading the server.

#### Linting and formatting

[CLI](/cli/overview) provides best effort to scaffold a reliable development workflow at scale. Thus, a generated Nest project comes with both a code **linter** and **formatter** preinstalled (respectively [eslint](https://eslint.org/) and [prettier](https://prettier.io/)).

> info **Hint** Not sure about the role of formatters vs linters? Learn the difference [here](https://prettier.io/docs/en/comparison.html).

To ensure maximum stability and extensibility, we use the base [`eslint`](https://www.npmjs.com/package/eslint) and [`prettier`](https://www.npmjs.com/package/prettier) cli packages. This setup allows neat IDE integration with official extensions by design.

For headless environments where an IDE is not relevant (Continuous Integration, Git hooks, etc.) a Nest project comes with ready-to-use `npm` scripts.

```bash
# Lint and autofix with eslint
$ npm run lint

# Format with prettier
$ npm run format
```

"""

NEST_JS_MODULES = """

### Modules

A module is a class annotated with a `@Module()` decorator. The `@Module()` decorator provides metadata that **Nest** makes use of to organize the application structure.

<figure><img src="/assets/Modules_1.png" /></figure>

Each application has at least one module, a **root module**. The root module is the starting point Nest uses to build the **application graph** - the internal data structure Nest uses to resolve module and provider relationships and dependencies. While very small applications may theoretically have just the root module, this is not the typical case. We want to emphasize that modules are **strongly** recommended as an effective way to organize your components. Thus, for most applications, the resulting architecture will employ multiple modules, each encapsulating a closely related set of **capabilities**.

The `@Module()` decorator takes a single object whose properties describe the module:

|               |                                                                                                                                                                                                          |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `providers`   | the providers that will be instantiated by the Nest injector and that may be shared at least across this module                                                                                          |
| `controllers` | the set of controllers defined in this module which have to be instantiated                                                                                                                              |
| `imports`     | the list of imported modules that export the providers which are required in this module                                                                                                                 |
| `exports`     | the subset of `providers` that are provided by this module and should be available in other modules which import this module. You can use either the provider itself or just its token (`provide` value) |

The module **encapsulates** providers by default. This means that it's impossible to inject providers that are neither directly part of the current module nor exported from the imported modules. Thus, you may consider the exported providers from a module as the module's public interface, or API.

#### Feature modules

The `CatsController` and `CatsService` belong to the same application domain. As they are closely related, it makes sense to move them into a feature module. A feature module simply organizes code relevant for a specific feature, keeping code organized and establishing clear boundaries. This helps us manage complexity and develop with [SOLID](https://en.wikipedia.org/wiki/SOLID) principles, especially as the size of the application and/or team grow.

To demonstrate this, we'll create the `CatsModule`.

```typescript
@@filename(cats/cats.module)
import { Module } from '@nestjs/common';
import { CatsController } from './cats.controller';
import { CatsService } from './cats.service';

@Module({
  controllers: [CatsController],
  providers: [CatsService],
})
export class CatsModule {}
```

> info **Hint** To create a module using the CLI, simply execute the `$ nest g module cats` command.

Above, we defined the `CatsModule` in the `cats.module.ts` file, and moved everything related to this module into the `cats` directory. The last thing we need to do is import this module into the root module (the `AppModule`, defined in the `app.module.ts` file).

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { CatsModule } from './cats/cats.module';

@Module({
  imports: [CatsModule],
})
export class AppModule {}
```

Here is how our directory structure looks now:

<div class="file-tree">
  <div class="item">src</div>
  <div class="children">
    <div class="item">cats</div>
    <div class="children">
      <div class="item">dto</div>
      <div class="children">
        <div class="item">create-cat.dto.ts</div>
      </div>
      <div class="item">interfaces</div>
      <div class="children">
        <div class="item">cat.interface.ts</div>
      </div>
      <div class="item">cats.controller.ts</div>
      <div class="item">cats.module.ts</div>
      <div class="item">cats.service.ts</div>
    </div>
    <div class="item">app.module.ts</div>
    <div class="item">main.ts</div>
  </div>
</div>

#### Shared modules

In Nest, modules are **singletons** by default, and thus you can share the same instance of any provider between multiple modules effortlessly.

<figure><img src="/assets/Shared_Module_1.png" /></figure>

Every module is automatically a **shared module**. Once created it can be reused by any module. Let's imagine that we want to share an instance of the `CatsService` between several other modules. In order to do that, we first need to **export** the `CatsService` provider by adding it to the module's `exports` array, as shown below:

```typescript
@@filename(cats.module)
import { Module } from '@nestjs/common';
import { CatsController } from './cats.controller';
import { CatsService } from './cats.service';

@Module({
  controllers: [CatsController],
  providers: [CatsService],
  exports: [CatsService]
})
export class CatsModule {}
```

Now any module that imports the `CatsModule` has access to the `CatsService` and will share the same instance with all other modules that import it as well.

<app-banner-devtools></app-banner-devtools>

#### Module re-exporting

As seen above, Modules can export their internal providers. In addition, they can re-export modules that they import. In the example below, the `CommonModule` is both imported into **and** exported from the `CoreModule`, making it available for other modules which import this one.

```typescript
@Module({
  imports: [CommonModule],
  exports: [CommonModule],
})
export class CoreModule {}
```

#### Dependency injection

A module class can **inject** providers as well (e.g., for configuration purposes):

```typescript
@@filename(cats.module)
import { Module } from '@nestjs/common';
import { CatsController } from './cats.controller';
import { CatsService } from './cats.service';

@Module({
  controllers: [CatsController],
  providers: [CatsService],
})
export class CatsModule {
  constructor(private catsService: CatsService) {}
}
@@switch
import { Module, Dependencies } from '@nestjs/common';
import { CatsController } from './cats.controller';
import { CatsService } from './cats.service';

@Module({
  controllers: [CatsController],
  providers: [CatsService],
})
@Dependencies(CatsService)
export class CatsModule {
  constructor(catsService) {
    this.catsService = catsService;
  }
}
```

However, module classes themselves cannot be injected as providers due to [circular dependency](/fundamentals/circular-dependency) .

#### Global modules

If you have to import the same set of modules everywhere, it can get tedious. Unlike in Nest, [Angular](https://angular.io) `providers` are registered in the global scope. Once defined, they're available everywhere. Nest, however, encapsulates providers inside the module scope. You aren't able to use a module's providers elsewhere without first importing the encapsulating module.

When you want to provide a set of providers which should be available everywhere out-of-the-box (e.g., helpers, database connections, etc.), make the module **global** with the `@Global()` decorator.

```typescript
import { Module, Global } from '@nestjs/common';
import { CatsController } from './cats.controller';
import { CatsService } from './cats.service';

@Global()
@Module({
  controllers: [CatsController],
  providers: [CatsService],
  exports: [CatsService],
})
export class CatsModule {}
```

The `@Global()` decorator makes the module global-scoped. Global modules should be registered **only once**, generally by the root or core module. In the above example, the `CatsService` provider will be ubiquitous, and modules that wish to inject the service will not need to import the `CatsModule` in their imports array.

> info **Hint** Making everything global is not a good design decision. Global modules are available to reduce the amount of necessary boilerplate. The `imports` array is generally the preferred way to make the module's API available to consumers.

#### Dynamic modules

The Nest module system includes a powerful feature called **dynamic modules**. This feature enables you to easily create customizable modules that can register and configure providers dynamically. Dynamic modules are covered extensively [here](/fundamentals/dynamic-modules). In this chapter, we'll give a brief overview to complete the introduction to modules.

Following is an example of a dynamic module definition for a `DatabaseModule`:

```typescript
@@filename()
import { Module, DynamicModule } from '@nestjs/common';
import { createDatabaseProviders } from './database.providers';
import { Connection } from './connection.provider';

@Module({
  providers: [Connection],
})
export class DatabaseModule {
  static forRoot(entities = [], options?): DynamicModule {
    const providers = createDatabaseProviders(options, entities);
    return {
      module: DatabaseModule,
      providers: providers,
      exports: providers,
    };
  }
}
@@switch
import { Module } from '@nestjs/common';
import { createDatabaseProviders } from './database.providers';
import { Connection } from './connection.provider';

@Module({
  providers: [Connection],
})
export class DatabaseModule {
  static forRoot(entities = [], options) {
    const providers = createDatabaseProviders(options, entities);
    return {
      module: DatabaseModule,
      providers: providers,
      exports: providers,
    };
  }
}
```

> info **Hint** The `forRoot()` method may return a dynamic module either synchronously or asynchronously (i.e., via a `Promise`).

This module defines the `Connection` provider by default (in the `@Module()` decorator metadata), but additionally - depending on the `entities` and `options` objects passed into the `forRoot()` method - exposes a collection of providers, for example, repositories. Note that the properties returned by the dynamic module **extend** (rather than override) the base module metadata defined in the `@Module()` decorator. That's how both the statically declared `Connection` provider **and** the dynamically generated repository providers are exported from the module.

If you want to register a dynamic module in the global scope, set the `global` property to `true`.

```typescript
{
  global: true,
  module: DatabaseModule,
  providers: providers,
  exports: providers,
}
```

> warning **Warning** As mentioned above, making everything global **is not a good design decision**.

The `DatabaseModule` can be imported and configured in the following manner:

```typescript
import { Module } from '@nestjs/common';
import { DatabaseModule } from './database/database.module';
import { User } from './users/entities/user.entity';

@Module({
  imports: [DatabaseModule.forRoot([User])],
})
export class AppModule {}
```

If you want to in turn re-export a dynamic module, you can omit the `forRoot()` method call in the exports array:

```typescript
import { Module } from '@nestjs/common';
import { DatabaseModule } from './database/database.module';
import { User } from './users/entities/user.entity';

@Module({
  imports: [DatabaseModule.forRoot([User])],
  exports: [DatabaseModule],
})
export class AppModule {}
```

The [Dynamic modules](/fundamentals/dynamic-modules) chapter covers this topic in greater detail, and includes a [working example](https://github.com/nestjs/nest/tree/master/sample/25-dynamic-modules).

> info **Hint** Learn how to build highly customizable dynamic modules with the use of `ConfigurableModuleBuilder` here in [this chapter](/fundamentals/dynamic-modules#configurable-module-builder).
"""

NEST_JS_SQL = """
### Database

Nest is database agnostic, allowing you to easily integrate with any SQL or NoSQL database. You have a number of options available to you, depending on your preferences. At the most general level, connecting Nest to a database is simply a matter of loading an appropriate Node.js driver for the database, just as you would with [Express](https://expressjs.com/en/guide/database-integration.html) or Fastify.

You can also directly use any general purpose Node.js database integration **library** or ORM, such as [MikroORM](https://mikro-orm.io/) (see [MikroORM recipe](/recipes/mikroorm)), [Sequelize](https://sequelize.org/) (see [Sequelize integration](/techniques/database#sequelize-integration)), [Knex.js](https://knexjs.org/) (see [Knex.js tutorial](https://dev.to/nestjs/build-a-nestjs-module-for-knex-js-or-other-resource-based-libraries-in-5-minutes-12an)), [TypeORM](https://github.com/typeorm/typeorm), and [Prisma](https://www.github.com/prisma/prisma) (see [Prisma recipe](/recipes/prisma)), to operate at a higher level of abstraction.

For convenience, Nest provides tight integration with TypeORM and Sequelize out-of-the-box with the `@nestjs/typeorm` and `@nestjs/sequelize` packages respectively, which we'll cover in the current chapter, and Mongoose with `@nestjs/mongoose`, which is covered in [this chapter](/techniques/mongodb). These integrations provide additional NestJS-specific features, such as model/repository injection, testability, and asynchronous configuration to make accessing your chosen database even easier.

### TypeORM Integration

For integrating with SQL and NoSQL databases, Nest provides the `@nestjs/typeorm` package. [TypeORM](https://github.com/typeorm/typeorm) is the most mature Object Relational Mapper (ORM) available for TypeScript. Since it's written in TypeScript, it integrates well with the Nest framework.

To begin using it, we first install the required dependencies. In this chapter, we'll demonstrate using the popular [MySQL](https://www.mysql.com/) Relational DBMS, but TypeORM provides support for many relational databases, such as PostgreSQL, Oracle, Microsoft SQL Server, SQLite, and even NoSQL databases like MongoDB. The procedure we walk through in this chapter will be the same for any database supported by TypeORM. You'll simply need to install the associated client API libraries for your selected database.

```bash
$ npm install --save @nestjs/typeorm typeorm mysql2
```

Once the installation process is complete, we can import the `TypeOrmModule` into the root `AppModule`.

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'root',
      database: 'test',
      entities: [],
      synchronize: true,
    }),
  ],
})
export class AppModule {}
```

> warning **Warning** Setting `synchronize: true` shouldn't be used in production - otherwise you can lose production data.

The `forRoot()` method supports all the configuration properties exposed by the `DataSource` constructor from the [TypeORM](https://typeorm.io/data-source-options#common-data-source-options) package. In addition, there are several extra configuration properties described below.

<table>
  <tr>
    <td><code>retryAttempts</code></td>
    <td>Number of attempts to connect to the database (default: <code>10</code>)</td>
  </tr>
  <tr>
    <td><code>retryDelay</code></td>
    <td>Delay between connection retry attempts (ms) (default: <code>3000</code>)</td>
  </tr>
  <tr>
    <td><code>autoLoadEntities</code></td>
    <td>If <code>true</code>, entities will be loaded automatically (default: <code>false</code>)</td>
  </tr>
</table>

> info **Hint** Learn more about the data source options [here](https://typeorm.io/data-source-options).

Once this is done, the TypeORM `DataSource` and `EntityManager` objects will be available to inject across the entire project (without needing to import any modules), for example:

```typescript
@@filename(app.module)
import { DataSource } from 'typeorm';

@Module({
  imports: [TypeOrmModule.forRoot(), UsersModule],
})
export class AppModule {
  constructor(private dataSource: DataSource) {}
}
@@switch
import { DataSource } from 'typeorm';

@Dependencies(DataSource)
@Module({
  imports: [TypeOrmModule.forRoot(), UsersModule],
})
export class AppModule {
  constructor(dataSource) {
    this.dataSource = dataSource;
  }
}
```

#### Repository pattern

[TypeORM](https://github.com/typeorm/typeorm) supports the **repository design pattern**, so each entity has its own repository. These repositories can be obtained from the database data source.

To continue the example, we need at least one entity. Let's define the `User` entity.

```typescript
@@filename(user.entity)
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  firstName: string;

  @Column()
  lastName: string;

  @Column({ default: true })
  isActive: boolean;
}
```

> info **Hint** Learn more about entities in the [TypeORM documentation](https://typeorm.io/#/entities).

The `User` entity file sits in the `users` directory. This directory contains all files related to the `UsersModule`. You can decide where to keep your model files, however, we recommend creating them near their **domain**, in the corresponding module directory.

To begin using the `User` entity, we need to let TypeORM know about it by inserting it into the `entities` array in the module `forRoot()` method options (unless you use a static glob path):

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from './users/user.entity';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'root',
      database: 'test',
      entities: [User],
      synchronize: true,
    }),
  ],
})
export class AppModule {}
```

Next, let's look at the `UsersModule`:

```typescript
@@filename(users.module)
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UsersService } from './users.service';
import { UsersController } from './users.controller';
import { User } from './user.entity';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  providers: [UsersService],
  controllers: [UsersController],
})
export class UsersModule {}
```

This module uses the `forFeature()` method to define which repositories are registered in the current scope. With that in place, we can inject the `UsersRepository` into the `UsersService` using the `@InjectRepository()` decorator:

```typescript
@@filename(users.service)
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './user.entity';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private usersRepository: Repository<User>,
  ) {}

  findAll(): Promise<User[]> {
    return this.usersRepository.find();
  }

  findOne(id: number): Promise<User | null> {
    return this.usersRepository.findOneBy({ id });
  }

  async remove(id: number): Promise<void> {
    await this.usersRepository.delete(id);
  }
}
@@switch
import { Injectable, Dependencies } from '@nestjs/common';
import { getRepositoryToken } from '@nestjs/typeorm';
import { User } from './user.entity';

@Injectable()
@Dependencies(getRepositoryToken(User))
export class UsersService {
  constructor(usersRepository) {
    this.usersRepository = usersRepository;
  }

  findAll() {
    return this.usersRepository.find();
  }

  findOne(id) {
    return this.usersRepository.findOneBy({ id });
  }

  async remove(id) {
    await this.usersRepository.delete(id);
  }
}
```

> warning **Notice** Don't forget to import the `UsersModule` into the root `AppModule`.

If you want to use the repository outside of the module which imports `TypeOrmModule.forFeature`, you'll need to re-export the providers generated by it.
You can do this by exporting the whole module, like this:

```typescript
@@filename(users.module)
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from './user.entity';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  exports: [TypeOrmModule]
})
export class UsersModule {}
```

Now if we import `UsersModule` in `UserHttpModule`, we can use `@InjectRepository(User)` in the providers of the latter module.

```typescript
@@filename(users-http.module)
import { Module } from '@nestjs/common';
import { UsersModule } from './users.module';
import { UsersService } from './users.service';
import { UsersController } from './users.controller';

@Module({
  imports: [UsersModule],
  providers: [UsersService],
  controllers: [UsersController]
})
export class UserHttpModule {}
```

#### Relations

Relations are associations established between two or more tables. Relations are based on common fields from each table, often involving primary and foreign keys.

There are three types of relations:

<table>
  <tr>
    <td><code>One-to-one</code></td>
    <td>Every row in the primary table has one and only one associated row in the foreign table.  Use the <code>@OneToOne()</code> decorator to define this type of relation.</td>
  </tr>
  <tr>
    <td><code>One-to-many / Many-to-one</code></td>
    <td>Every row in the primary table has one or more related rows in the foreign table. Use the <code>@OneToMany()</code> and <code>@ManyToOne()</code> decorators to define this type of relation.</td>
  </tr>
  <tr>
    <td><code>Many-to-many</code></td>
    <td>Every row in the primary table has many related rows in the foreign table, and every record in the foreign table has many related rows in the primary table. Use the <code>@ManyToMany()</code> decorator to define this type of relation.</td>
  </tr>
</table>

To define relations in entities, use the corresponding **decorators**. For example, to define that each `User` can have multiple photos, use the `@OneToMany()` decorator.

```typescript
@@filename(user.entity)
import { Entity, Column, PrimaryGeneratedColumn, OneToMany } from 'typeorm';
import { Photo } from '../photos/photo.entity';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  firstName: string;

  @Column()
  lastName: string;

  @Column({ default: true })
  isActive: boolean;

  @OneToMany(type => Photo, photo => photo.user)
  photos: Photo[];
}
```

> info **Hint** To learn more about relations in TypeORM, visit the [TypeORM documentation](https://typeorm.io/#/relations).

#### Auto-load entities

Manually adding entities to the `entities` array of the data source options can be tedious. In addition, referencing entities from the root module breaks application domain boundaries and causes leaking implementation details to other parts of the application. To address this issue, an alternative solution is provided. To automatically load entities, set the `autoLoadEntities` property of the configuration object (passed into the `forRoot()` method) to `true`, as shown below:

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      ...
      autoLoadEntities: true,
    }),
  ],
})
export class AppModule {}
```

With that option specified, every entity registered through the `forFeature()` method will be automatically added to the `entities` array of the configuration object.

> warning **Warning** Note that entities that aren't registered through the `forFeature()` method, but are only referenced from the entity (via a relationship), won't be included by way of the `autoLoadEntities` setting.

#### Separating entity definition

You can define an entity and its columns right in the model, using decorators. But some people prefer to define entities and their columns inside separate files using the ["entity schemas"](https://typeorm.io/#/separating-entity-definition).

```typescript
import { EntitySchema } from 'typeorm';
import { User } from './user.entity';

export const UserSchema = new EntitySchema<User>({
  name: 'User',
  target: User,
  columns: {
    id: {
      type: Number,
      primary: true,
      generated: true,
    },
    firstName: {
      type: String,
    },
    lastName: {
      type: String,
    },
    isActive: {
      type: Boolean,
      default: true,
    },
  },
  relations: {
    photos: {
      type: 'one-to-many',
      target: 'Photo', // the name of the PhotoSchema
    },
  },
});
```

> warning error **Warning** If you provide the `target` option, the `name` option value has to be the same as the name of the target class.
> If you do not provide the `target` you can use any name.

Nest allows you to use an `EntitySchema` instance wherever an `Entity` is expected, for example:

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserSchema } from './user.schema';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

@Module({
  imports: [TypeOrmModule.forFeature([UserSchema])],
  providers: [UsersService],
  controllers: [UsersController],
})
export class UsersModule {}
```

#### TypeORM Transactions

A database transaction symbolizes a unit of work performed within a database management system against a database, and treated in a coherent and reliable way independent of other transactions. A transaction generally represents any change in a database ([learn more](https://en.wikipedia.org/wiki/Database_transaction)).

There are many different strategies to handle [TypeORM transactions](https://typeorm.io/#/transactions). We recommend using the `QueryRunner` class because it gives full control over the transaction.

First, we need to inject the `DataSource` object into a class in the normal way:

```typescript
@Injectable()
export class UsersService {
  constructor(private dataSource: DataSource) {}
}
```

> info **Hint** The `DataSource` class is imported from the `typeorm` package.

Now, we can use this object to create a transaction.

```typescript
async createMany(users: User[]) {
  const queryRunner = this.dataSource.createQueryRunner();

  await queryRunner.connect();
  await queryRunner.startTransaction();
  try {
    await queryRunner.manager.save(users[0]);
    await queryRunner.manager.save(users[1]);

    await queryRunner.commitTransaction();
  } catch (err) {
    // since we have errors lets rollback the changes we made
    await queryRunner.rollbackTransaction();
  } finally {
    // you need to release a queryRunner which was manually instantiated
    await queryRunner.release();
  }
}
```

> info **Hint** Note that the `dataSource` is used only to create the `QueryRunner`. However, to test this class would require mocking the entire `DataSource` object (which exposes several methods). Thus, we recommend using a helper factory class (e.g., `QueryRunnerFactory`) and defining an interface with a limited set of methods required to maintain transactions. This technique makes mocking these methods pretty straightforward.

<app-banner-devtools></app-banner-devtools>

Alternatively, you can use the callback-style approach with the `transaction` method of the `DataSource` object ([read more](https://typeorm.io/#/transactions/creating-and-using-transactions)).

```typescript
async createMany(users: User[]) {
  await this.dataSource.transaction(async manager => {
    await manager.save(users[0]);
    await manager.save(users[1]);
  });
}
```

#### Subscribers

With TypeORM [subscribers](https://typeorm.io/#/listeners-and-subscribers/what-is-a-subscriber), you can listen to specific entity events.

```typescript
import {
  DataSource,
  EntitySubscriberInterface,
  EventSubscriber,
  InsertEvent,
} from 'typeorm';
import { User } from './user.entity';

@EventSubscriber()
export class UserSubscriber implements EntitySubscriberInterface<User> {
  constructor(dataSource: DataSource) {
    dataSource.subscribers.push(this);
  }

  listenTo() {
    return User;
  }

  beforeInsert(event: InsertEvent<User>) {
    console.log(`BEFORE USER INSERTED: `, event.entity);
  }
}
```

> error **Warning** Event subscribers can not be [request-scoped](/fundamentals/injection-scopes).

Now, add the `UserSubscriber` class to the `providers` array:

```typescript
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from './user.entity';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { UserSubscriber } from './user.subscriber';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  providers: [UsersService, UserSubscriber],
  controllers: [UsersController],
})
export class UsersModule {}
```

> info **Hint** Learn more about entity subscribers [here](https://typeorm.io/#/listeners-and-subscribers/what-is-a-subscriber).

#### Migrations

[Migrations](https://typeorm.io/#/migrations) provide a way to incrementally update the database schema to keep it in sync with the application's data model while preserving existing data in the database. To generate, run, and revert migrations, TypeORM provides a dedicated [CLI](https://typeorm.io/#/migrations/creating-a-new-migration).

Migration classes are separate from the Nest application source code. Their lifecycle is maintained by the TypeORM CLI. Therefore, you are not able to leverage dependency injection and other Nest specific features with migrations. To learn more about migrations, follow the guide in the [TypeORM documentation](https://typeorm.io/#/migrations/creating-a-new-migration).

#### Multiple databases

Some projects require multiple database connections. This can also be achieved with this module. To work with multiple connections, first create the connections. In this case, data source naming becomes **mandatory**.

Suppose you have an `Album` entity stored in its own database.

```typescript
const defaultOptions = {
  type: 'postgres',
  port: 5432,
  username: 'user',
  password: 'password',
  database: 'db',
  synchronize: true,
};

@Module({
  imports: [
    TypeOrmModule.forRoot({
      ...defaultOptions,
      host: 'user_db_host',
      entities: [User],
    }),
    TypeOrmModule.forRoot({
      ...defaultOptions,
      name: 'albumsConnection',
      host: 'album_db_host',
      entities: [Album],
    }),
  ],
})
export class AppModule {}
```

> warning **Notice** If you don't set the `name` for a data source, its name is set to `default`. Please note that you shouldn't have multiple connections without a name, or with the same name, otherwise they will get overridden.

> warning **Notice** If you are using `TypeOrmModule.forRootAsync`, you have to **also** set the data source name outside `useFactory`. For example:
>
> ```typescript
> TypeOrmModule.forRootAsync({
>   name: 'albumsConnection',
>   useFactory: ...,
>   inject: ...,
> }),
> ```
>
> See [this issue](https://github.com/nestjs/typeorm/issues/86) for more details.

At this point, you have `User` and `Album` entities registered with their own data source. With this setup, you have to tell the `TypeOrmModule.forFeature()` method and the `@InjectRepository()` decorator which data source should be used. If you do not pass any data source name, the `default` data source is used.

```typescript
@Module({
  imports: [
    TypeOrmModule.forFeature([User]),
    TypeOrmModule.forFeature([Album], 'albumsConnection'),
  ],
})
export class AppModule {}
```

You can also inject the `DataSource` or `EntityManager` for a given data source:

```typescript
@Injectable()
export class AlbumsService {
  constructor(
    @InjectDataSource('albumsConnection')
    private dataSource: DataSource,
    @InjectEntityManager('albumsConnection')
    private entityManager: EntityManager,
  ) {}
}
```

It's also possible to inject any `DataSource` to the providers:

```typescript
@Module({
  providers: [
    {
      provide: AlbumsService,
      useFactory: (albumsConnection: DataSource) => {
        return new AlbumsService(albumsConnection);
      },
      inject: [getDataSourceToken('albumsConnection')],
    },
  ],
})
export class AlbumsModule {}
```

#### Testing

When it comes to unit testing an application, we usually want to avoid making a database connection, keeping our test suites independent and their execution process as fast as possible. But our classes might depend on repositories that are pulled from the data source (connection) instance. How do we handle that? The solution is to create mock repositories. In order to achieve that, we set up [custom providers](/fundamentals/custom-providers). Each registered repository is automatically represented by an `<EntityName>Repository` token, where `EntityName` is the name of your entity class.

The `@nestjs/typeorm` package exposes the `getRepositoryToken()` function which returns a prepared token based on a given entity.

```typescript
@Module({
  providers: [
    UsersService,
    {
      provide: getRepositoryToken(User),
      useValue: mockRepository,
    },
  ],
})
export class UsersModule {}
```

Now a substitute `mockRepository` will be used as the `UsersRepository`. Whenever any class asks for `UsersRepository` using an `@InjectRepository()` decorator, Nest will use the registered `mockRepository` object.

#### Async configuration

You may want to pass your repository module options asynchronously instead of statically. In this case, use the `forRootAsync()` method, which provides several ways to deal with async configuration.

One approach is to use a factory function:

```typescript
TypeOrmModule.forRootAsync({
  useFactory: () => ({
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password: 'root',
    database: 'test',
    entities: [],
    synchronize: true,
  }),
});
```

Our factory behaves like any other [asynchronous provider](https://docs.nestjs.com/fundamentals/async-providers) (e.g., it can be `async` and it's able to inject dependencies through `inject`).

```typescript
TypeOrmModule.forRootAsync({
  imports: [ConfigModule],
  useFactory: (configService: ConfigService) => ({
    type: 'mysql',
    host: configService.get('HOST'),
    port: +configService.get('PORT'),
    username: configService.get('USERNAME'),
    password: configService.get('PASSWORD'),
    database: configService.get('DATABASE'),
    entities: [],
    synchronize: true,
  }),
  inject: [ConfigService],
});
```

Alternatively, you can use the `useClass` syntax:

```typescript
TypeOrmModule.forRootAsync({
  useClass: TypeOrmConfigService,
});
```

The construction above will instantiate `TypeOrmConfigService` inside `TypeOrmModule` and use it to provide an options object by calling `createTypeOrmOptions()`. Note that this means that the `TypeOrmConfigService` has to implement the `TypeOrmOptionsFactory` interface, as shown below:

```typescript
@Injectable()
export class TypeOrmConfigService implements TypeOrmOptionsFactory {
  createTypeOrmOptions(): TypeOrmModuleOptions {
    return {
      type: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'root',
      database: 'test',
      entities: [],
      synchronize: true,
    };
  }
}
```

In order to prevent the creation of `TypeOrmConfigService` inside `TypeOrmModule` and use a provider imported from a different module, you can use the `useExisting` syntax.

```typescript
TypeOrmModule.forRootAsync({
  imports: [ConfigModule],
  useExisting: ConfigService,
});
```

This construction works the same as `useClass` with one critical difference - `TypeOrmModule` will lookup imported modules to reuse an existing `ConfigService` instead of instantiating a new one.

> info **Hint** Make sure that the `name` property is defined at the same level as the `useFactory`, `useClass`, or `useValue` property. This will allow Nest to properly register the data source under the appropriate injection token.

#### Custom DataSource Factory

In conjunction with async configuration using `useFactory`, `useClass`, or `useExisting`, you can optionally specify a `dataSourceFactory` function which will allow you to provide your own TypeORM data source rather than allowing `TypeOrmModule` to create the data source.

`dataSourceFactory` receives the TypeORM `DataSourceOptions` configured during async configuration using `useFactory`, `useClass`, or `useExisting` and returns a `Promise` that resolves a TypeORM `DataSource`.

```typescript
TypeOrmModule.forRootAsync({
  imports: [ConfigModule],
  inject: [ConfigService],
  // Use useFactory, useClass, or useExisting
  // to configure the DataSourceOptions.
  useFactory: (configService: ConfigService) => ({
    type: 'mysql',
    host: configService.get('HOST'),
    port: +configService.get('PORT'),
    username: configService.get('USERNAME'),
    password: configService.get('PASSWORD'),
    database: configService.get('DATABASE'),
    entities: [],
    synchronize: true,
  }),
  // dataSource receives the configured DataSourceOptions
  // and returns a Promise<DataSource>.
  dataSourceFactory: async (options) => {
    const dataSource = await new DataSource(options).initialize();
    return dataSource;
  },
});
```

> info **Hint** The `DataSource` class is imported from the `typeorm` package.

#### Example

A working example is available [here](https://github.com/nestjs/nest/tree/master/sample/05-sql-typeorm).

<app-banner-enterprise></app-banner-enterprise>

### Sequelize Integration

An alternative to using TypeORM is to use the [Sequelize](https://sequelize.org/) ORM with the `@nestjs/sequelize` package. In addition, we leverage the [sequelize-typescript](https://github.com/RobinBuschmann/sequelize-typescript) package which provides a set of additional decorators to declaratively define entities.

To begin using it, we first install the required dependencies. In this chapter, we'll demonstrate using the popular [MySQL](https://www.mysql.com/) Relational DBMS, but Sequelize provides support for many relational databases, such as PostgreSQL, MySQL, Microsoft SQL Server, SQLite, and MariaDB. The procedure we walk through in this chapter will be the same for any database supported by Sequelize. You'll simply need to install the associated client API libraries for your selected database.

```bash
$ npm install --save @nestjs/sequelize sequelize sequelize-typescript mysql2
$ npm install --save-dev @types/sequelize
```

Once the installation process is complete, we can import the `SequelizeModule` into the root `AppModule`.

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { SequelizeModule } from '@nestjs/sequelize';

@Module({
  imports: [
    SequelizeModule.forRoot({
      dialect: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'root',
      database: 'test',
      models: [],
    }),
  ],
})
export class AppModule {}
```

The `forRoot()` method supports all the configuration properties exposed by the Sequelize constructor ([read more](https://sequelize.org/v5/manual/getting-started.html#setting-up-a-connection)). In addition, there are several extra configuration properties described below.

<table>
  <tr>
    <td><code>retryAttempts</code></td>
    <td>Number of attempts to connect to the database (default: <code>10</code>)</td>
  </tr>
  <tr>
    <td><code>retryDelay</code></td>
    <td>Delay between connection retry attempts (ms) (default: <code>3000</code>)</td>
  </tr>
  <tr>
    <td><code>autoLoadModels</code></td>
    <td>If <code>true</code>, models will be loaded automatically (default: <code>false</code>)</td>
  </tr>
  <tr>
    <td><code>keepConnectionAlive</code></td>
    <td>If <code>true</code>, connection will not be closed on the application shutdown (default: <code>false</code>)</td>
  </tr>
  <tr>
    <td><code>synchronize</code></td>
    <td>If <code>true</code>, automatically loaded models will be synchronized (default: <code>true</code>)</td>
  </tr>
</table>

Once this is done, the `Sequelize` object will be available to inject across the entire project (without needing to import any modules), for example:

```typescript
@@filename(app.service)
import { Injectable } from '@nestjs/common';
import { Sequelize } from 'sequelize-typescript';

@Injectable()
export class AppService {
  constructor(private sequelize: Sequelize) {}
}
@@switch
import { Injectable } from '@nestjs/common';
import { Sequelize } from 'sequelize-typescript';

@Dependencies(Sequelize)
@Injectable()
export class AppService {
  constructor(sequelize) {
    this.sequelize = sequelize;
  }
}
```

#### Models

Sequelize implements the Active Record pattern. With this pattern, you use model classes directly to interact with the database. To continue the example, we need at least one model. Let's define the `User` model.

```typescript
@@filename(user.model)
import { Column, Model, Table } from 'sequelize-typescript';

@Table
export class User extends Model {
  @Column
  firstName: string;

  @Column
  lastName: string;

  @Column({ defaultValue: true })
  isActive: boolean;
}
```

> info **Hint** Learn more about the available decorators [here](https://github.com/RobinBuschmann/sequelize-typescript#column).

The `User` model file sits in the `users` directory. This directory contains all files related to the `UsersModule`. You can decide where to keep your model files, however, we recommend creating them near their **domain**, in the corresponding module directory.

To begin using the `User` model, we need to let Sequelize know about it by inserting it into the `models` array in the module `forRoot()` method options:

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { SequelizeModule } from '@nestjs/sequelize';
import { User } from './users/user.model';

@Module({
  imports: [
    SequelizeModule.forRoot({
      dialect: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'root',
      database: 'test',
      models: [User],
    }),
  ],
})
export class AppModule {}
```

Next, let's look at the `UsersModule`:

```typescript
@@filename(users.module)
import { Module } from '@nestjs/common';
import { SequelizeModule } from '@nestjs/sequelize';
import { User } from './user.model';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

@Module({
  imports: [SequelizeModule.forFeature([User])],
  providers: [UsersService],
  controllers: [UsersController],
})
export class UsersModule {}
```

This module uses the `forFeature()` method to define which models are registered in the current scope. With that in place, we can inject the `UserModel` into the `UsersService` using the `@InjectModel()` decorator:

```typescript
@@filename(users.service)
import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/sequelize';
import { User } from './user.model';

@Injectable()
export class UsersService {
  constructor(
    @InjectModel(User)
    private userModel: typeof User,
  ) {}

  async findAll(): Promise<User[]> {
    return this.userModel.findAll();
  }

  findOne(id: string): Promise<User> {
    return this.userModel.findOne({
      where: {
        id,
      },
    });
  }

  async remove(id: string): Promise<void> {
    const user = await this.findOne(id);
    await user.destroy();
  }
}
@@switch
import { Injectable, Dependencies } from '@nestjs/common';
import { getModelToken } from '@nestjs/sequelize';
import { User } from './user.model';

@Injectable()
@Dependencies(getModelToken(User))
export class UsersService {
  constructor(usersRepository) {
    this.usersRepository = usersRepository;
  }

  async findAll() {
    return this.userModel.findAll();
  }

  findOne(id) {
    return this.userModel.findOne({
      where: {
        id,
      },
    });
  }

  async remove(id) {
    const user = await this.findOne(id);
    await user.destroy();
  }
}
```

> warning **Notice** Don't forget to import the `UsersModule` into the root `AppModule`.

If you want to use the repository outside of the module which imports `SequelizeModule.forFeature`, you'll need to re-export the providers generated by it.
You can do this by exporting the whole module, like this:

```typescript
@@filename(users.module)
import { Module } from '@nestjs/common';
import { SequelizeModule } from '@nestjs/sequelize';
import { User } from './user.entity';

@Module({
  imports: [SequelizeModule.forFeature([User])],
  exports: [SequelizeModule]
})
export class UsersModule {}
```

Now if we import `UsersModule` in `UserHttpModule`, we can use `@InjectModel(User)` in the providers of the latter module.

```typescript
@@filename(users-http.module)
import { Module } from '@nestjs/common';
import { UsersModule } from './users.module';
import { UsersService } from './users.service';
import { UsersController } from './users.controller';

@Module({
  imports: [UsersModule],
  providers: [UsersService],
  controllers: [UsersController]
})
export class UserHttpModule {}
```

#### Relations

Relations are associations established between two or more tables. Relations are based on common fields from each table, often involving primary and foreign keys.

There are three types of relations:

<table>
  <tr>
    <td><code>One-to-one</code></td>
    <td>Every row in the primary table has one and only one associated row in the foreign table</td>
  </tr>
  <tr>
    <td><code>One-to-many / Many-to-one</code></td>
    <td>Every row in the primary table has one or more related rows in the foreign table</td>
  </tr>
  <tr>
    <td><code>Many-to-many</code></td>
    <td>Every row in the primary table has many related rows in the foreign table, and every record in the foreign table has many related rows in the primary table</td>
  </tr>
</table>

To define relations in models, use the corresponding **decorators**. For example, to define that each `User` can have multiple photos, use the `@HasMany()` decorator.

```typescript
@@filename(user.model)
import { Column, Model, Table, HasMany } from 'sequelize-typescript';
import { Photo } from '../photos/photo.model';

@Table
export class User extends Model {
  @Column
  firstName: string;

  @Column
  lastName: string;

  @Column({ defaultValue: true })
  isActive: boolean;

  @HasMany(() => Photo)
  photos: Photo[];
}
```

> info **Hint** To learn more about associations in Sequelize, read [this](https://github.com/RobinBuschmann/sequelize-typescript#model-association) chapter.

#### Auto-load models

Manually adding models to the `models` array of the connection options can be tedious. In addition, referencing models from the root module breaks application domain boundaries and causes leaking implementation details to other parts of the application. To solve this issue, automatically load models by setting both `autoLoadModels` and `synchronize` properties of the configuration object (passed into the `forRoot()` method) to `true`, as shown below:

```typescript
@@filename(app.module)
import { Module } from '@nestjs/common';
import { SequelizeModule } from '@nestjs/sequelize';

@Module({
  imports: [
    SequelizeModule.forRoot({
      ...
      autoLoadModels: true,
      synchronize: true,
    }),
  ],
})
export class AppModule {}
```

With that option specified, every model registered through the `forFeature()` method will be automatically added to the `models` array of the configuration object.

> warning **Warning** Note that models that aren't registered through the `forFeature()` method, but are only referenced from the model (via an association), won't be included.

#### Sequelize Transactions

A database transaction symbolizes a unit of work performed within a database management system against a database, and treated in a coherent and reliable way independent of other transactions. A transaction generally represents any change in a database ([learn more](https://en.wikipedia.org/wiki/Database_transaction)).

There are many different strategies to handle [Sequelize transactions](https://sequelize.org/v5/manual/transactions.html). Below is a sample implementation of a managed transaction (auto-callback).

First, we need to inject the `Sequelize` object into a class in the normal way:

```typescript
@Injectable()
export class UsersService {
  constructor(private sequelize: Sequelize) {}
}
```

> info **Hint** The `Sequelize` class is imported from the `sequelize-typescript` package.

Now, we can use this object to create a transaction.

```typescript
async createMany() {
  try {
    await this.sequelize.transaction(async t => {
      const transactionHost = { transaction: t };

      await this.userModel.create(
          { firstName: 'Abraham', lastName: 'Lincoln' },
          transactionHost,
      );
      await this.userModel.create(
          { firstName: 'John', lastName: 'Boothe' },
          transactionHost,
      );
    });
  } catch (err) {
    // Transaction has been rolled back
    // err is whatever rejected the promise chain returned to the transaction callback
  }
}
```

> info **Hint** Note that the `Sequelize` instance is used only to start the transaction. However, to test this class would require mocking the entire `Sequelize` object (which exposes several methods). Thus, we recommend using a helper factory class (e.g., `TransactionRunner`) and defining an interface with a limited set of methods required to maintain transactions. This technique makes mocking these methods pretty straightforward.

#### Migrations

[Migrations](https://sequelize.org/v5/manual/migrations.html) provide a way to incrementally update the database schema to keep it in sync with the application's data model while preserving existing data in the database. To generate, run, and revert migrations, Sequelize provides a dedicated [CLI](https://sequelize.org/v5/manual/migrations.html#the-cli).

Migration classes are separate from the Nest application source code. Their lifecycle is maintained by the Sequelize CLI. Therefore, you are not able to leverage dependency injection and other Nest specific features with migrations. To learn more about migrations, follow the guide in the [Sequelize documentation](https://sequelize.org/v5/manual/migrations.html#the-cli).

<app-banner-courses></app-banner-courses>

#### Multiple databases

Some projects require multiple database connections. This can also be achieved with this module. To work with multiple connections, first create the connections. In this case, connection naming becomes **mandatory**.

Suppose you have an `Album` entity stored in its own database.

```typescript
const defaultOptions = {
  dialect: 'postgres',
  port: 5432,
  username: 'user',
  password: 'password',
  database: 'db',
  synchronize: true,
};

@Module({
  imports: [
    SequelizeModule.forRoot({
      ...defaultOptions,
      host: 'user_db_host',
      models: [User],
    }),
    SequelizeModule.forRoot({
      ...defaultOptions,
      name: 'albumsConnection',
      host: 'album_db_host',
      models: [Album],
    }),
  ],
})
export class AppModule {}
```

> warning **Notice** If you don't set the `name` for a connection, its name is set to `default`. Please note that you shouldn't have multiple connections without a name, or with the same name, otherwise they will get overridden.

At this point, you have `User` and `Album` models registered with their own connection. With this setup, you have to tell the `SequelizeModule.forFeature()` method and the `@InjectModel()` decorator which connection should be used. If you do not pass any connection name, the `default` connection is used.

```typescript
@Module({
  imports: [
    SequelizeModule.forFeature([User]),
    SequelizeModule.forFeature([Album], 'albumsConnection'),
  ],
})
export class AppModule {}
```

You can also inject the `Sequelize` instance for a given connection:

```typescript
@Injectable()
export class AlbumsService {
  constructor(
    @InjectConnection('albumsConnection')
    private sequelize: Sequelize,
  ) {}
}
```

It's also possible to inject any `Sequelize` instance to the providers:

```typescript
@Module({
  providers: [
    {
      provide: AlbumsService,
      useFactory: (albumsSequelize: Sequelize) => {
        return new AlbumsService(albumsSequelize);
      },
      inject: [getDataSourceToken('albumsConnection')],
    },
  ],
})
export class AlbumsModule {}
```

#### Testing

When it comes to unit testing an application, we usually want to avoid making a database connection, keeping our test suites independent and their execution process as fast as possible. But our classes might depend on models that are pulled from the connection instance. How do we handle that? The solution is to create mock models. In order to achieve that, we set up [custom providers](/fundamentals/custom-providers). Each registered model is automatically represented by a `<ModelName>Model` token, where `ModelName` is the name of your model class.

The `@nestjs/sequelize` package exposes the `getModelToken()` function which returns a prepared token based on a given model.

```typescript
@Module({
  providers: [
    UsersService,
    {
      provide: getModelToken(User),
      useValue: mockModel,
    },
  ],
})
export class UsersModule {}
```

Now a substitute `mockModel` will be used as the `UserModel`. Whenever any class asks for `UserModel` using an `@InjectModel()` decorator, Nest will use the registered `mockModel` object.

#### Async configuration

You may want to pass your `SequelizeModule` options asynchronously instead of statically. In this case, use the `forRootAsync()` method, which provides several ways to deal with async configuration.

One approach is to use a factory function:

```typescript
SequelizeModule.forRootAsync({
  useFactory: () => ({
    dialect: 'mysql',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password: 'root',
    database: 'test',
    models: [],
  }),
});
```

Our factory behaves like any other [asynchronous provider](https://docs.nestjs.com/fundamentals/async-providers) (e.g., it can be `async` and it's able to inject dependencies through `inject`).

```typescript
SequelizeModule.forRootAsync({
  imports: [ConfigModule],
  useFactory: (configService: ConfigService) => ({
    dialect: 'mysql',
    host: configService.get('HOST'),
    port: +configService.get('PORT'),
    username: configService.get('USERNAME'),
    password: configService.get('PASSWORD'),
    database: configService.get('DATABASE'),
    models: [],
  }),
  inject: [ConfigService],
});
```

Alternatively, you can use the `useClass` syntax:

```typescript
SequelizeModule.forRootAsync({
  useClass: SequelizeConfigService,
});
```

The construction above will instantiate `SequelizeConfigService` inside `SequelizeModule` and use it to provide an options object by calling `createSequelizeOptions()`. Note that this means that the `SequelizeConfigService` has to implement the `SequelizeOptionsFactory` interface, as shown below:

```typescript
@Injectable()
class SequelizeConfigService implements SequelizeOptionsFactory {
  createSequelizeOptions(): SequelizeModuleOptions {
    return {
      dialect: 'mysql',
      host: 'localhost',
      port: 3306,
      username: 'root',
      password: 'root',
      database: 'test',
      models: [],
    };
  }
}
```

In order to prevent the creation of `SequelizeConfigService` inside `SequelizeModule` and use a provider imported from a different module, you can use the `useExisting` syntax.

```typescript
SequelizeModule.forRootAsync({
  imports: [ConfigModule],
  useExisting: ConfigService,
});
```

This construction works the same as `useClass` with one critical difference - `SequelizeModule` will lookup imported modules to reuse an existing `ConfigService` instead of instantiating a new one.

#### Example

A working example is available [here](https://github.com/nestjs/nest/tree/master/sample/07-sequelize).

"""

NEST_JS_CRUD_GEN = """
### CRUD generator

Throughout the life span of a project, when we build new features, we often need to add new resources to our application. These resources typically require multiple, repetitive operations that we have to repeat each time we define a new resource.

#### Introduction

Let's imagine a real-world scenario, where we need to expose CRUD endpoints for 2 entities, let's say **User** and **Product** entities.
Following the best practices, for each entity we would have to perform several operations, as follows:

- Generate a module (`nest g mo`) to keep code organized and establish clear boundaries (grouping related components)
- Generate a controller (`nest g co`) to define CRUD routes (or queries/mutations for GraphQL applications)
- Generate a service (`nest g s`) to implement & isolate business logic
- Generate an entity class/interface to represent the resource data shape
- Generate Data Transfer Objects (or inputs for GraphQL applications) to define how the data will be sent over the network

That's a lot of steps!

To help speed up this repetitive process, [Nest CLI](/cli/overview) provides a generator (schematic) that automatically generates all the boilerplate code to help us avoid doing all of this, and make the developer experience much simpler.

> info **Note** The schematic supports generating **HTTP** controllers, **Microservice** controllers, **GraphQL** resolvers (both code first and schema first), and **WebSocket** Gateways.

#### Generating a new resource

To create a new resource, simply run the following command in the root directory of your project:

```shell
$ nest g resource
```

`nest g resource` command not only generates all the NestJS building blocks (module, service, controller classes) but also an entity class, DTO classes as well as the testing (`.spec`) files.

Below you can see the generated controller file (for REST API):

```typescript
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  create(@Body() createUserDto: CreateUserDto) {
    return this.usersService.create(createUserDto);
  }

  @Get()
  findAll() {
    return this.usersService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.usersService.findOne(+id);
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() updateUserDto: UpdateUserDto) {
    return this.usersService.update(+id, updateUserDto);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.usersService.remove(+id);
  }
}
```

Also, it automatically creates placeholders for all the CRUD endpoints (routes for REST APIs, queries and mutations for GraphQL, message subscribes for both Microservices and WebSocket Gateways) - all without having to lift a finger.

> warning **Note** Generated service classes are **not** tied to any specific **ORM (or data source)**. This makes the generator generic enough to meet the needs of any project. By default, all methods will contain placeholders, allowing you to populate it with the data sources specific to your project.

Likewise, if you want to generate resolvers for a GraphQL application, simply select the `GraphQL (code first)` (or `GraphQL (schema first)`) as your transport layer.

In this case, NestJS will generate a resolver class instead of a REST API controller:

```shell
$ nest g resource users

> ? What transport layer do you use? GraphQL (code first)
> ? Would you like to generate CRUD entry points? Yes
> CREATE src/users/users.module.ts (224 bytes)
> CREATE src/users/users.resolver.spec.ts (525 bytes)
> CREATE src/users/users.resolver.ts (1109 bytes)
> CREATE src/users/users.service.spec.ts (453 bytes)
> CREATE src/users/users.service.ts (625 bytes)
> CREATE src/users/dto/create-user.input.ts (195 bytes)
> CREATE src/users/dto/update-user.input.ts (281 bytes)
> CREATE src/users/entities/user.entity.ts (187 bytes)
> UPDATE src/app.module.ts (312 bytes)
```

> info **Hint** To avoid generating test files, you can pass the `--no-spec` flag, as follows: `nest g resource users --no-spec`

We can see below, that not only were all boilerplate mutations and queries created, but everything is all tied together. We're utilizing the `UsersService`, `User` Entity, and our DTO's.

```typescript
import { Resolver, Query, Mutation, Args, Int } from '@nestjs/graphql';
import { UsersService } from './users.service';
import { User } from './entities/user.entity';
import { CreateUserInput } from './dto/create-user.input';
import { UpdateUserInput } from './dto/update-user.input';

@Resolver(() => User)
export class UsersResolver {
  constructor(private readonly usersService: UsersService) {}

  @Mutation(() => User)
  createUser(@Args('createUserInput') createUserInput: CreateUserInput) {
    return this.usersService.create(createUserInput);
  }

  @Query(() => [User], { name: 'users' })
  findAll() {
    return this.usersService.findAll();
  }

  @Query(() => User, { name: 'user' })
  findOne(@Args('id', { type: () => Int }) id: number) {
    return this.usersService.findOne(id);
  }

  @Mutation(() => User)
  updateUser(@Args('updateUserInput') updateUserInput: UpdateUserInput) {
    return this.usersService.update(updateUserInput.id, updateUserInput);
  }

  @Mutation(() => User)
  removeUser(@Args('id', { type: () => Int }) id: number) {
    return this.usersService.remove(id);
  }
}
```

"""

NEST_JS_CLI_RULES = """
### CLI command reference

#### nest new

Creates a new (standard mode) Nest project.

```bash
$ nest new <name> [options]
$ nest n <name> [options]
```

##### Description

Creates and initializes a new Nest project. Prompts for package manager.

- Creates a folder with the given `<name>`
- Populates the folder with configuration files
- Creates sub-folders for source code (`/src`) and end-to-end tests (`/test`)
- Populates the sub-folders with default files for app components and tests

##### Arguments

| Argument | Description                 |
| -------- | --------------------------- |
| `<name>` | The name of the new project |

##### Options

| Option                                | Description                                                                                                                                                                                          |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--dry-run`                           | Reports changes that would be made, but does not change the filesystem.<br/> Alias: `-d`                                                                                                             |
| `--skip-git`                          | Skip git repository initialization.<br/> Alias: `-g`                                                                                                                                                 |
| `--skip-install`                      | Skip package installation.<br/> Alias: `-s`                                                                                                                                                          |
| `--package-manager [package-manager]` | Specify package manager. Use `npm`, `yarn`, or `pnpm`. Package manager must be installed globally.<br/> Alias: `-p`                                                                                  |
| `--language [language]`               | Specify programming language (`TS` or `JS`).<br/> Alias: `-l`                                                                                                                                        |
| `--collection [collectionName]`       | Specify schematics collection. Use package name of installed npm package containing schematic.<br/> Alias: `-c`                                                                                      |
| `--strict`                            | Start the project with the following TypeScript compiler flags enabled: `strictNullChecks`, `noImplicitAny`, `strictBindCallApply`, `forceConsistentCasingInFileNames`, `noFallthroughCasesInSwitch` |

#### nest generate

Generates and/or modifies files based on a schematic

```bash
$ nest generate <schematic> <name> [options]
$ nest g <schematic> <name> [options]
```

##### Arguments

| Argument      | Description                                                                                              |
| ------------- | -------------------------------------------------------------------------------------------------------- |
| `<schematic>` | The `schematic` or `collection:schematic` to generate. See the table below for the available schematics. |
| `<name>`      | The name of the generated component.                                                                     |

##### Schematics

| Name          | Alias | Description                                                                                                  |
| ------------- | ----- | ------------------------------------------------------------------------------------------------------------ |
| `app`         |       | Generate a new application within a monorepo (converting to monorepo if it's a standard structure).          |
| `library`     | `lib` | Generate a new library within a monorepo (converting to monorepo if it's a standard structure).              |
| `class`       | `cl`  | Generate a new class.                                                                                        |
| `controller`  | `co`  | Generate a controller declaration.                                                                           |
| `decorator`   | `d`   | Generate a custom decorator.                                                                                 |
| `filter`      | `f`   | Generate a filter declaration.                                                                               |
| `gateway`     | `ga`  | Generate a gateway declaration.                                                                              |
| `guard`       | `gu`  | Generate a guard declaration.                                                                                |
| `interface`   | `itf` | Generate an interface.                                                                                       |
| `interceptor` | `itc` | Generate an interceptor declaration.                                                                         |
| `middleware`  | `mi`  | Generate a middleware declaration.                                                                           |
| `module`      | `mo`  | Generate a module declaration.                                                                               |
| `pipe`        | `pi`  | Generate a pipe declaration.                                                                                 |
| `provider`    | `pr`  | Generate a provider declaration.                                                                             |
| `resolver`    | `r`   | Generate a resolver declaration.                                                                             |
| `resource`    | `res` | Generate a new CRUD resource. See the [CRUD (resource) generator](/recipes/crud-generator) for more details. |
| `service`     | `s`   | Generate a service declaration.                                                                              |

##### Options

| Option                          | Description                                                                                                     |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `--dry-run`                     | Reports changes that would be made, but does not change the filesystem.<br/> Alias: `-d`                        |
| `--project [project]`           | Project that element should be added to.<br/> Alias: `-p`                                                       |
| `--flat`                        | Do not generate a folder for the element.                                                                       |
| `--collection [collectionName]` | Specify schematics collection. Use package name of installed npm package containing schematic.<br/> Alias: `-c` |
| `--spec`                        | Enforce spec files generation (default)                                                                         |
| `--no-spec`                     | Disable spec files generation                                                                                   |

#### nest build

Compiles an application or workspace into an output folder.

Also, the `build` command is responsible for:

- mapping paths (if using path aliases) via `tsconfig-paths`
- annotating DTOs with OpenAPI decorators (if `@nestjs/swagger` CLI plugin is enabled)
- annotating DTOs with GraphQL decorators (if `@nestjs/graphql` CLI plugin is enabled)

```bash
$ nest build <name> [options]
```

##### Arguments

| Argument | Description                       |
| -------- | --------------------------------- |
| `<name>` | The name of the project to build. |

##### Options

| Option             | Description                                                                                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--path [path]`    | Path to `tsconfig` file. <br/>Alias `-p`                                                                                                                                                   |
| `--config [path]`  | Path to `nest-cli` configuration file. <br/>Alias `-c`                                                                                                                                     |
| `--watch`          | Run in watch mode (live-reload).<br /> If you're using `tsc` for compilation, you can type `rs` to restart the application (when `manualRestart` option is set to `true`). <br/>Alias `-w` |
| `--builder [name]` | Specify the builder to use for compilation (`tsc`, `swc`, or `webpack`). <br/>Alias `-b`                                                                                                   |
| `--webpack`        | Use webpack for compilation (deprecated: use `--builder webpack` instead).                                                                                                                 |
| `--webpackPath`    | Path to webpack configuration.                                                                                                                                                             |
| `--tsc`            | Force use `tsc` for compilation.                                                                                                                                                           |

#### nest start

Compiles and runs an application (or default project in a workspace).

```bash
$ nest start <name> [options]
```

##### Arguments

| Argument | Description                     |
| -------- | ------------------------------- |
| `<name>` | The name of the project to run. |

##### Options

| Option                  | Description                                                                                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `--path [path]`         | Path to `tsconfig` file. <br/>Alias `-p`                                                                             |
| `--config [path]`       | Path to `nest-cli` configuration file. <br/>Alias `-c`                                                               |
| `--watch`               | Run in watch mode (live-reload) <br/>Alias `-w`                                                                      |
| `--builder [name]`      | Specify the builder to use for compilation (`tsc`, `swc`, or `webpack`). <br/>Alias `-b`                             |
| `--preserveWatchOutput` | Keep outdated console output in watch mode instead of clearing the screen. (`tsc` watch mode only)                   |
| `--watchAssets`         | Run in watch mode (live-reload), watching non-TS files (assets). See [Assets](cli/monorepo#assets) for more details. |
| `--debug [hostport]`    | Run in debug mode (with --inspect flag) <br/>Alias `-d`                                                              |
| `--webpack`             | Use webpack for compilation. (deprecated: use `--builder webpack` instead)                                           |
| `--webpackPath`         | Path to webpack configuration.                                                                                       |
| `--tsc`                 | Force use `tsc` for compilation.                                                                                     |
| `--exec [binary]`       | Binary to run (default: `node`). <br/>Alias `-e`                                                                     |

#### nest add

Imports a library that has been packaged as a **nest library**, running its install schematic.

```bash
$ nest add <name> [options]
```

##### Arguments

| Argument | Description                        |
| -------- | ---------------------------------- |
| `<name>` | The name of the library to import. |

#### nest info

Displays information about installed nest packages and other helpful system info. For example:

```bash
$ nest info
```

```bash
 _   _             _      ___  _____  _____  _     _____
| \ | |           | |    |_  |/  ___|/  __ \| |   |_   _|
|  \| |  ___  ___ | |_     | |\ `--. | /  \/| |     | |
| . ` | / _ \/ __|| __|    | | `--. \| |    | |     | |
| |\  ||  __/\__ \| |_ /\__/ //\__/ /| \__/\| |_____| |_
\_| \_/ \___||___/ \__|\____/ \____/  \____/\_____/\___/

[System Information]
OS Version : macOS High Sierra
NodeJS Version : v16.18.0
[Nest Information]
microservices version : 10.0.0
websockets version : 10.0.0
testing version : 10.0.0
common version : 10.0.0
core version : 10.0.0
```
"""